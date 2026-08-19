"""
Вспомогательные утилиты для модуля game.
Содержит функции парсинга, валидации данных и обработки ошибок.
"""
import json
import logging
import traceback
import os

from django.core.files.storage import default_storage
from django.db import InternalError
from django.http import JsonResponse

from .models import get_memory_game_image_path, get_sound_loto_image_path, get_sound_loto_audio_path

logger = logging.getLogger(__name__)

# Допустимые форматы файлов
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg']
MAX_AUDIO_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ в байтах


def parse_and_validate_puzzle_data(post_data: dict, files_data: dict = None) -> dict:
    """
    Парсит и валидирует данные для сохранения/обновления пазла из FormData.
    
    Args:
        post_data (dict): Данные из request.POST или распарсенного MultiPartParser.
        files_data (dict, optional): Данные из request.FILES или распарсенного MultiPartParser.
        
    Returns:
        dict: Словарь с валидированными данными:
            - name (str): Название пазла.
            - grid_size (int): Размер сетки.
            - piece_positions (list[int]): Позиции элементов.
            - preset_path (str | None): Путь к пресету.
            - uploaded_image_file (InMemoryUploadedFile | None): Загруженный файл.
            
    Raises:
        ValueError: Если данные некорректны или отсутствуют.
    """
    if files_data is None:
        files_data = {}
        
    name = post_data.get('name', '').strip()
    if not name:
        raise ValueError("Название не может быть пустым.")
        
    grid_size_str = post_data.get('gridSize')
    try:
        grid_size = int(grid_size_str)
        if grid_size < 2:
            raise ValueError("Размер сетки слишком мал.")
    except (TypeError, ValueError):
        raise ValueError("Неверный или отсутствующий размер сетки.")
        
    piece_positions_str = post_data.get('piecePositions')
    if not piece_positions_str:
        raise ValueError("Данные о позициях элементов отсутствуют.")
        
    try:
        piece_positions = json.loads(piece_positions_str)
        if not isinstance(piece_positions, list) or not all(isinstance(p, int) for p in piece_positions):
            raise ValueError("Позиции должны быть списком целых чисел.")
        expected_length = grid_size * grid_size
        if len(piece_positions) != expected_length:
            raise ValueError(f"Количество позиций ({len(piece_positions)}) не соответствует размеру сетки ({expected_length}).")
    except json.JSONDecodeError as e:
        raise ValueError(f"Неверный формат JSON в позициях элементов: {e}")
        
    preset_path = post_data.get('preset_image_path')
    uploaded_image_file = files_data.get('user_image_file')
    
    return {
        'name': name,
        'grid_size': grid_size,
        'piece_positions': piece_positions,
        'preset_path': preset_path,
        'uploaded_image_file': uploaded_image_file
    }


def parse_and_validate_memory_game_data(post_data: dict, files_data: dict = None) -> dict:
    """
    Парсит и валидирует данные для сохранения/обновления игры "Поиск пар" из FormData.
    
    Args:
        post_data (dict): Данные из request.POST или распарсенного MultiPartParser.
        files_data (dict, optional): Данные из request.FILES или распарсенного MultiPartParser.
        
    Returns:
        dict: Словарь с валидированными данными:
            - name (str): Название игры.
            - pair_count (int): Количество пар.
            - card_layout (list[int]): Расположение карточек.
            - preset_name (str | None): Название пресета.
            - custom_images (list): Список загруженных файлов.
            
    Raises:
        ValueError: Если данные некорректны или отсутствуют.
    """
    if files_data is None:
        files_data = {}
        
    name = post_data.get('name', '').strip()
    if not name:
        raise ValueError("Название не может быть пустым.")
    
    try:
        pair_count = int(post_data.get('pairCount', 0))
        if not (2 <= pair_count <= 50):
            raise ValueError("Неверное количество пар.")
    except (TypeError, ValueError):
        raise ValueError("Неверное или отсутствующее количество пар.")
        
    card_layout_str = post_data.get('cardLayout', '[]')
    try:
        card_layout = json.loads(card_layout_str)
        if not (isinstance(card_layout, list) and len(card_layout) == pair_count * 2 and all(isinstance(i, int) for i in card_layout)):
            raise ValueError("Некорректные данные о расположении карточек.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Неверный формат JSON в расположении карточек: {e}")
        
    preset_name = post_data.get('presetName') or None
    
    # Поддержка как QueryDict (request.FILES), так и обычного dict (из MultiPartParser)
    if hasattr(files_data, 'getlist'):
        custom_images = files_data.getlist('customImages[]')
    else:
        custom_images = files_data.get('customImages[]', [])
    
    return {
        'name': name,
        'pair_count': pair_count,
        'card_layout': card_layout,
        'preset_name': preset_name,
        'custom_images': custom_images
    }


def parse_and_validate_sound_loto_data(post_data: dict, files_data: dict = None, is_update: bool = False) -> dict:
    """
    Парсит и валидирует данные для сохранения/обновления игры "Звуковое лото" из FormData.

    Args:
        post_data (dict): Данные из request.POST или распарсенного MultiPartParser.
        files_data (dict, optional): Данные из request.FILES или распарсенного MultiPartParser.
        is_update (bool): Флаг обновления. При True не требует пресет или файлы.

    Returns:
        dict: Словарь с валидированными данными:
            - name (str): Название игры.
            - rounds_count (int): Количество раундов.
            - cards_count (int): Количество карточек на экране.
            - autoplay (bool): Автовоспроизведение звука.
            - show_labels (bool): Показывать подписи.
            - preset_name (str | None): Название пресета.
            - custom_images (list): Список загруженных изображений.
            - custom_audios (list): Список загруженных аудиофайлов.
            - custom_labels (list[str]): Список подписей.
            - audio_order (list[int] | None): Новый порядок аудио (для перестановки без пере-загрузки).

    Raises:
        ValueError: Если данные некорректны или отсутствуют.
    """
    if files_data is None:
        files_data = {}

    # Валидация названия
    name = post_data.get('name', '').strip()
    if not name:
        raise ValueError("Название не может быть пустым.")

    # Валидация количества раундов
    try:
        rounds_count = int(post_data.get('roundsCount', 4))
        if not (2 <= rounds_count <= 6):
            raise ValueError("Количество раундов должно быть от 2 до 6.")
    except (TypeError, ValueError):
        raise ValueError("Неверное или отсутствующее количество раундов.")

    # Валидация количества карточек
    try:
        cards_count = int(post_data.get('cardsCount', 4))
        if cards_count not in [2, 3, 4, 6]:
            raise ValueError("Количество карточек должно быть 2, 3, 4 или 6.")
    except (TypeError, ValueError):
        raise ValueError("Неверное или отсутствующее количество карточек.")

    # Валидация булевых параметров
    autoplay = post_data.get('autoplay', 'true').lower() == 'true'
    show_labels = post_data.get('showLabels', 'true').lower() == 'true'

    # Валидация пресета
    preset_name = post_data.get('presetName') or None

    # Получение файлов
    if hasattr(files_data, 'getlist'):
        custom_images = files_data.getlist('customImages[]')
        custom_audios = files_data.getlist('customAudios[]')
    else:
        custom_images = files_data.get('customImages[]', [])
        custom_audios = files_data.get('customAudios[]', [])

    # Получение подписей
    custom_labels_str = post_data.get('customLabels', '[]')
    try:
        custom_labels = json.loads(custom_labels_str)
        if not isinstance(custom_labels, list) or not all(isinstance(label, str) for label in custom_labels):
            raise ValueError("Подписи должны быть списком строк.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Неверный формат JSON в подписях: {e}")

    # Получение порядка аудио (для перестановки без пере-загрузки файлов)
    audio_order_str = post_data.get('audioOrder')
    audio_order = None
    if audio_order_str:
        try:
            audio_order = json.loads(audio_order_str)
            if not isinstance(audio_order, list) or not all(isinstance(i, int) for i in audio_order):
                raise ValueError("Порядок аудио должен быть списком целых чисел.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Неверный формат JSON в порядке аудио: {e}")

    # Проверка взаимоисключаемости пресета и пользовательских файлов
    is_custom_set = bool(custom_images) or bool(custom_audios)
    if preset_name and is_custom_set:
        raise ValueError("Нельзя одновременно указать пресет и загрузить свои файлы.")

    if not is_update and not preset_name and not is_custom_set:
        raise ValueError("Необходимо выбрать пресет или загрузить свои файлы.")

    # Валидация пользовательских файлов
    if is_custom_set:
        # Проверка количества файлов
        if len(custom_images) != len(custom_audios):
            raise ValueError(
                f"Количество изображений ({len(custom_images)}) не совпадает с количеством аудиофайлов ({len(custom_audios)})."
            )

        if len(custom_labels) != len(custom_images):
            raise ValueError(
                f"Количество подписей ({len(custom_labels)}) не совпадает с количеством изображений ({len(custom_images)})."
            )

        # Проверка достаточности пар
        pairs_count = len(custom_images)
        required_count = max(rounds_count, cards_count)
        if pairs_count < required_count:
            raise ValueError(
                f"Недостаточно пар для игры. Требуется минимум {required_count}, а загружено {pairs_count}."
            )

        # Валидация форматов и размеров файлов
        for i, image_file in enumerate(custom_images):
            image_ext = os.path.splitext(image_file.name)[1].lower()
            if image_ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"Недопустимый формат изображения №{i + 1}. Допустимые форматы: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
                )

        for i, audio_file in enumerate(custom_audios):
            audio_ext = os.path.splitext(audio_file.name)[1].lower()
            if audio_ext not in ALLOWED_AUDIO_EXTENSIONS:
                raise ValueError(
                    f"Недопустимый формат аудиофайла №{i + 1}. Допустимые форматы: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}."
                )

            # Проверка размера аудиофайла
            if audio_file.size > MAX_AUDIO_FILE_SIZE:
                raise ValueError(
                    f"Аудиофайл №{i + 1} превышает максимальный размер {MAX_AUDIO_FILE_SIZE // (1024 * 1024)} МБ."
                )

    return {
        'name': name,
        'rounds_count': rounds_count,
        'cards_count': cards_count,
        'autoplay': autoplay,
        'show_labels': show_labels,
        'preset_name': preset_name,
        'custom_images': custom_images,
        'custom_audios': custom_audios,
        'custom_labels': custom_labels,
        'audio_order': audio_order,
    }


def handle_db_integrity_error(error: InternalError, game_type: str, name: str, extra_info: str = "") -> JsonResponse:
    """
    Обрабатывает ошибки целостности БД (InternalError), вызванные триггерами уникальности.
    
    Args:
        error (InternalError): Исключение, полученное от БД.
        game_type (str): Тип игры ('puzzle', 'memory_game' или 'sound_loto').
        name (str): Название игры, которое пытались сохранить.
        extra_info (str, optional): Дополнительная информация для сообщения об ошибке.
        
    Returns:
        JsonResponse: Ответ с сообщением об ошибке (статус 400) или внутренняя ошибка (статус 500).
    """
    db_error_message = str(error).lower()
    
    if game_type == 'puzzle':
        trigger_part1 = 'пазл с названием'
        trigger_part2 = 'уже существует'
        error_detail = f'Пазл с названием "{name}" {extra_info} уже существует.'
    elif game_type == 'memory_game':
        trigger_part1 = 'игра "поиск пар" с названием'
        trigger_part2 = 'уже существует'
        error_detail = f'"Поиск пар" с названием "{name}" {extra_info} уже существует.'
    elif game_type == 'sound_loto':
        trigger_part1 = 'игра "звуковое лото" с названием'
        trigger_part2 = 'уже существует'
        error_detail = f'"Звуковое лото" с названием "{name}" {extra_info} уже существует.'
    else:
        trigger_part1 = ''
        trigger_part2 = ''
        error_detail = 'Произошла ошибка базы данных.'
        
    if trigger_part1 in db_error_message and trigger_part2 in db_error_message:
        logger.warning(f"Ошибка уникальности {game_type}: {error_detail} | Оригинальная ошибка: {error}")
        return JsonResponse({'status': 'error', 'message': error_detail}, status=400)
    else:
        logger.error(f"Непредвиденная ошибка целостности БД при сохранении {game_type}: {error.__class__.__name__}: {error}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла ошибка базы данных. Попробуйте позже.'
        }, status=500)


def cleanup_uploaded_files(file_paths: list) -> None:
    """
    Безопасно удаляет список файлов из хранилища.
    
    Args:
        file_paths (list): Список путей к файлам для удаления.
    """
    for path in file_paths:
        if path and default_storage.exists(path):
            try:
                default_storage.delete(path)
                logger.info(f"Временный файл успешно удален: {path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {path}: {e}")


def cleanup_sound_loto_custom_files(custom_pairs: list) -> None:
    """
    Удаляет все файлы (изображения и аудио) из списка пользовательских пар "Звукового лото".
    
    Args:
        custom_pairs (list): Список словарей с ключами 'image' и 'audio'.
    """
    file_paths = []
    for pair in custom_pairs:
        if pair.get('image'):
            file_paths.append(pair['image'])
        if pair.get('audio'):
            file_paths.append(pair['audio'])
    cleanup_uploaded_files(file_paths)


def save_memory_game_custom_images(custom_images: list, pair_count: int) -> list:
    """
    Сохраняет пользовательские изображения для игры "Поиск пар" в хранилище.
    
    Args:
        custom_images (list): Список загруженных файлов.
        pair_count (int): Необходимое количество пар (и изображений).
        
    Returns:
        list: Список путей к сохраненным файлам.
        
    Raises:
        ValueError: Если количество изображений меньше необходимого.
    """
    if len(custom_images) < pair_count:
        raise ValueError(f'Недостаточно пользовательских изображений. Загружено {len(custom_images)}, требуется {pair_count}.')
    
    saved_paths = []
    for file in custom_images:
        file_path = get_memory_game_image_path(None, file.name)
        saved_path = default_storage.save(file_path, file)
        saved_paths.append(saved_path)
    
    return saved_paths


def save_sound_loto_custom_files(custom_images: list, custom_audios: list, custom_labels: list) -> list:
    """
    Сохраняет пользовательские файлы (изображения, аудио и подписи) для игры "Звуковое лото" в хранилище.
    
    Args:
        custom_images (list): Список загруженных изображений.
        custom_audios (list): Список загруженных аудиофайлов.
        custom_labels (list): Список подписей.
        
    Returns:
        list: Список словарей с путями к сохраненным файлам и подписями:
            [{"image": "path/to/image.jpg", "audio": "path/to/audio.mp3", "label": "Подпись"}, ...]
            
    Raises:
        ValueError: Если количество файлов не совпадает.
    """
    if len(custom_images) != len(custom_audios) or len(custom_images) != len(custom_labels):
        raise ValueError("Количество изображений, аудиофайлов и подписей должно совпадать.")
    
    saved_pairs = []
    for image_file, audio_file, label in zip(custom_images, custom_audios, custom_labels):
        image_path = get_sound_loto_image_path(None, image_file.name)
        saved_image_path = default_storage.save(image_path, image_file)
        
        audio_path = get_sound_loto_audio_path(None, audio_file.name)
        saved_audio_path = default_storage.save(audio_path, audio_file)
        
        saved_pairs.append({
            'image': saved_image_path,
            'audio': saved_audio_path,
            'label': label
        })
    
    return saved_pairs

