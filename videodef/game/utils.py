"""
Вспомогательные утилиты для модуля game.
Содержит функции парсинга, валидации данных и обработки ошибок.
"""
import json
import logging
import traceback

from django.core.files.storage import default_storage
from django.db import InternalError
from django.http import JsonResponse

from .models import get_memory_game_image_path

logger = logging.getLogger(__name__)


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
    if not grid_size_str:
        raise ValueError("Неверный или отсутствующий размер сетки.")
    try:
        grid_size = int(grid_size_str)
    except (TypeError, ValueError):
        raise ValueError("Неверный или отсутствующий размер сетки.")
        
    if grid_size < 2:
        raise ValueError("Размер сетки слишком мал.")
        
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
        
    pair_count_str = post_data.get('pairCount')
    if not pair_count_str:
        raise ValueError("Неверное или отсутствующее количество пар.")
    try:
        pair_count = int(pair_count_str)
    except (TypeError, ValueError):
        raise ValueError("Неверное или отсутствующее количество пар.")

    if not (2 <= pair_count <= 50):
        raise ValueError("Неверное количество пар.")
        
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


def handle_db_integrity_error(error: InternalError, game_type: str, name: str, extra_info: str = "") -> JsonResponse:
    """
    Обрабатывает ошибки целостности БД (InternalError), вызванные триггерами уникальности.
    
    Args:
        error (InternalError): Исключение, полученное от БД.
        game_type (str): Тип игры ('puzzle' или 'memory_game').
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