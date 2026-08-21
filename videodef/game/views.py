"""
Модуль views для приложения game.
Содержит представления для отображения игр, сохранения/загрузки/обновления/удаления игр.
"""
import logging
import traceback

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.db import transaction, InternalError
from django.db.models import Value, CharField, OuterRef, Subquery, F
from django.db.models.functions import Concat, Coalesce
from django.http import JsonResponse, Http404
from django.http.multipartparser import MultiPartParser
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from io import BytesIO

from .models import UserGame, UserPuzzle, UserMemoryGame, UserSoundLoto, Genre
from .utils import (
    parse_and_validate_puzzle_data,
    parse_and_validate_memory_game_data,
    parse_and_validate_sound_loto_data,
    handle_db_integrity_error,
    cleanup_uploaded_files,
    cleanup_sound_loto_custom_files,
    save_memory_game_custom_images,
    save_sound_loto_custom_files
)

logger = logging.getLogger(__name__)


def games(request):
    """Отображает главную страницу со списком доступных игр."""
    games_list = [
        {"title": "Интерактивная доска",
         "description": "Интерактивная доска для совместного рисования и работы с изображениями в реальном времени. Поддерживает многопользовательский режим, перетаскивание и масштабирование картинок.",
         "image": "images/board.png",
         "url": "game:whiteboard"},
        {"title": "Пазлы",
         "description": "Увлекательная игра, которая поможет развить внимание, логику и пространственное восприятие. В этой игре вам предстоит собирать изображения, разделенные на кусочки, и восстанавливать их в правильном порядке.",
         "image": "images/Puzzle_game.png",
         "url": "game:puzzle_game"},
        {"title": "Поиск пар",
         "description": "Классическая игра на развитие памяти и концентрации. Открывайте карточки, запоминайте расположение уникальных изображений и находите совпадающие пары.",
         "image": "images/Memory_game.png",
         "url": "game:memory_game"},
        {"title": "Звуковое лото",
         "description": "Игра на развитие слухового восприятия и внимания. Прослушайте звук и найдите соответствующую карточку среди предложенных вариантов. Используйте готовые наборы или загрузите свои изображения и аудио.",
         "image": "images/Sound_loto.png",
         "url": "game:sound_loto"},
    ]
    return render(request, "game/game_main.html", {"games": games_list})


def puzzle_game(request):
    """Отображает страницу отдельной игры 'Пазлы'."""
    return render(request, "game/puzzles.html")


def memory_game(request):
    """Отображает страницу отдельной игры 'Поиск пар'."""
    return render(request, "game/memory_game.html")


def sound_loto(request):
    """Отображает страницу отдельной игры 'Звуковое лото'."""
    return render(request, "game/sound_loto.html")


def whiteboard(request):
    """Отображает страницу интерактивной доски."""
    return render(request, "game/whiteboard.html")


@login_required
def my_games_view(request):
    """
    Отображает страницу 'Мои игры' с фильтрацией и сортировкой.
    """
    puzzle_name_subquery = UserPuzzle.objects.filter(game_id=OuterRef('pk')).values('name')[:1]
    memory_game_name_subquery = UserMemoryGame.objects.filter(game_id=OuterRef('pk')).values('name')[:1]
    sound_loto_name_subquery = UserSoundLoto.objects.filter(game_id=OuterRef('pk')).values('name')[:1]
    
    user_games_query = UserGame.objects.filter(user=request.user).select_related('genre').annotate(
        display_name=Coalesce(
            Subquery(puzzle_name_subquery, output_field=CharField(null=True)),
            Subquery(memory_game_name_subquery, output_field=CharField(null=True)),
            Subquery(sound_loto_name_subquery, output_field=CharField(null=True)),
            Concat(F('genre__name'), Value(' ('), F('game_id'), Value(')'))
        )
    )

    # --- Обработка фильтра по жанру ---
    genres_for_filter = Genre.objects.all().order_by('name')
    selected_genre_id = request.GET.get('genre')
    if selected_genre_id:
        user_games_query = user_games_query.filter(genre__id=selected_genre_id)

    # --- Обработка сортировки ---
    sort_by_param = request.GET.get('sort_by', 'created')
    sort_order_param = request.GET.get('order', 'desc')
    valid_sort_fields = {'name': 'display_name', 'genre': 'genre__name', 'created': 'created_at', 'updated': 'updated_at'}
    sort_field_db = valid_sort_fields.get(sort_by_param, 'created_at')

    if sort_order_param == 'desc':
        user_games_query = user_games_query.order_by(F(sort_field_db).desc(nulls_last=True))
    else:
        user_games_query = user_games_query.order_by(F(sort_field_db).asc(nulls_last=True))

    # Выполняем запрос
    user_games_list = list(user_games_query)

    # --- Добавление URL изображений игр ---
    puzzle_game_pks = [game.pk for game in user_games_list if game.genre.code == 'PZL']
    memory_game_pks = [game.pk for game in user_games_list if game.genre.code == 'MEM']
    sound_loto_pks = [game.pk for game in user_games_list if game.genre.code == 'SLT']

    puzzle_details_map = {}
    if puzzle_game_pks:
        puzzles_data = UserPuzzle.objects.filter(game_id__in=puzzle_game_pks).only('game_id', 'preset_image_path', 'user_image')
        for p_data in puzzles_data:
            puzzle_details_map[p_data.game_id] = p_data.image_url

    memory_game_details_map = {}
    if memory_game_pks:
        for game_pk in memory_game_pks:
            details = UserMemoryGame.objects.get(pk=game_pk)
            if details.custom_image_paths and details.custom_image_paths[0]:
                memory_game_details_map[game_pk] = default_storage.url(details.custom_image_paths[0])
            elif details.preset_name:
                try:
                    base_path = settings.STATIC_URL + 'images/memory_game_presets/'
                    if details.preset_name == 'fruits':
                        memory_game_details_map[game_pk] = base_path + 'fruits/apple.png'
                    elif details.preset_name == 'animals':
                        memory_game_details_map[game_pk] = base_path + 'animals/panda.png'
                    else:
                        memory_game_details_map[game_pk] = static('images/Memory_game_icon.png')
                except Exception:
                    memory_game_details_map[game_pk] = static('images/Memory_game_icon.png')
    
    sound_loto_details_map = {}
    if sound_loto_pks:
        for game_pk in sound_loto_pks:
            details = UserSoundLoto.objects.get(pk=game_pk)
            sound_loto_details_map[game_pk] = details.first_image_url
    
    for game_obj in user_games_list:
        if game_obj.genre.code == 'PZL':
            game_obj.display_image_url = puzzle_details_map.get(game_obj.pk)
        elif game_obj.genre.code == 'MEM':
            game_obj.display_image_url = memory_game_details_map.get(game_obj.pk)
        elif game_obj.genre.code == 'SLT':
            game_obj.display_image_url = sound_loto_details_map.get(game_obj.pk)
        else:
            game_obj.display_image_url = None


    context = {
        'user_games': user_games_list,
        'genres_for_filter': genres_for_filter,
        'current_filters': {'genre': selected_genre_id},
        'current_sort': {'by': sort_by_param, 'order': sort_order_param}
    }
    return render(request, "game/my_games.html", context)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def delete_game_view(request, game_id: str):
    """
    Удаляет игру с указанным game_id, принадлежащую текущему пользователю.
    """
    try:
        game_to_delete = get_object_or_404(
            UserGame.objects.select_related('puzzle_details', 'memory_game_details', 'sound_loto_details'), 
            pk=game_id, 
            user=request.user
        )
        
        display_name = game_to_delete.game_id
        if hasattr(game_to_delete, 'puzzle_details') and game_to_delete.puzzle_details:
            display_name = game_to_delete.puzzle_details.name
        elif hasattr(game_to_delete, 'memory_game_details') and game_to_delete.memory_game_details:
            display_name = game_to_delete.memory_game_details.name
        elif hasattr(game_to_delete, 'sound_loto_details') and game_to_delete.sound_loto_details:
            display_name = game_to_delete.sound_loto_details.name
            
        game_to_delete.delete()
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Игра "{display_name}" успешно удалена.'
        })
        
    except Http404:
        return JsonResponse({
            'status': 'error',
            'message': 'Игра не найдена или у вас нет прав на ее удаление.'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Ошибка при удалении игры {game_id}: {e}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error', 
            'message': 'Произошла ошибка при удалении игры.'
        }, status=500)


@login_required
@require_POST
def save_puzzle_view(request):
    """
    Обрабатывает POST-запрос для сохранения состояния игры-пазла для текущего пользователя.
    """
    puzzle = None
    try:
        puzzle_genre = Genre.objects.get(code='PZL')
    except Genre.DoesNotExist:
        logger.critical("Жанр 'Пазл' (код PZL) не найден в базе данных!")
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка конфигурации сервера: Жанр пазлов отсутствует в базе данных'
        }, status=500)
    
    try:
        data = parse_and_validate_puzzle_data(request.POST, request.FILES)
        
        if data['preset_path'] and data['uploaded_image_file']:
            return JsonResponse({'status': 'error', 'message': 'Нельзя одновременно указать пресет и загрузить файл.'}, status=400)
        if not data['preset_path'] and not data['uploaded_image_file']:
            return JsonResponse({'status': 'error', 'message': 'Необходимо выбрать пресет или загрузить изображение.'}, status=400)
        
        with transaction.atomic():
            new_game = UserGame(user=request.user, genre=puzzle_genre)
            new_game.save()
            
            puzzle = UserPuzzle(
                game=new_game,
                name=data['name'],
                grid_size=data['grid_size'],
                piece_positions=data['piece_positions'],
                preset_image_path=data['preset_path'] if data['preset_path'] else None,
                user_image=data['uploaded_image_file'] if data['uploaded_image_file'] else None
            )
            puzzle.full_clean()
            puzzle.save()
        
        return JsonResponse({'status': 'success', 'message': f'Пазл "{data["name"]}" успешно сохранен!'})
        
    except ValueError as e:
        logger.warning(f"Ошибка валидации при сохранении пазла: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    except ValidationError as e:
        error_message = '; '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        logger.warning(f"Ошибка валидации модели при сохранении пазла: {e.message_dict}")
        return JsonResponse({'status': 'error', 'message': f'Ошибка введенных данных: {error_message}'}, status=400)
        
    except InternalError as e:
        if puzzle and puzzle.user_image and puzzle.user_image.name:
            if default_storage.exists(puzzle.user_image.name):
                puzzle.user_image.delete(save=False)
        return handle_db_integrity_error(e, 'puzzle', data.get('name', ''), f'и размером сетки {data.get("grid_size", 0)}x{data.get("grid_size", 0)}')
        
    except Exception as e:
        if puzzle and puzzle.user_image and puzzle.user_image.name:
            if default_storage.exists(puzzle.user_image.name):
                puzzle.user_image.delete(save=False)
        logger.error(f"Непредвиденная ошибка при сохранении пазла ({request.user.username}): {e.__class__.__name__}: {e}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при сохранении пазла. Попробуйте позже.'
        }, status=500)


@login_required
@require_GET
def load_puzzles_view(request):
    """
    Обрабатывает GET-запрос для получения списка всех сохраненных пазлов для текущего пользователя.
    """
    try:
        puzzle_genre = Genre.objects.get(code='PZL')
    except Genre.DoesNotExist:
        logger.critical("Жанр 'Пазл' (код PZL) не найден в базе данных!")
        return JsonResponse({'status': 'success', 'puzzles': []})
    
    try:
        # --- Запрос к базе данных ---
        puzzles = UserPuzzle.objects.filter(
            game__user=request.user,
            game__genre=puzzle_genre
        ).select_related('game').order_by('-game__created_at')

        # --- Формирование ответа ---
        data_list = []
        for p in puzzles:
            data_list.append({
                'id': p.pk,
                'name': p.name,
                'grid_size': p.grid_size,
                'image_url': p.image_url,
                'preset_path': p.preset_image_path,
                'has_user_image': bool(p.user_image),
                'piece_positions': p.piece_positions
            })
        return JsonResponse({'status': 'success', 'puzzles': data_list})
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка пазлов ({request.user.username}): {e.__class__.__name__}: {e}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при загрузке списка пазлов.'
        }, status=500)


@login_required
@require_http_methods(["PUT"])
def update_puzzle_view(request, game_id: str):
    """
    Обрабатывает PUT-запрос для обновления существующего пазла.
    """
    old_puzzle_file_to_delete = None
    try:
        user_puzzle = get_object_or_404(UserPuzzle, game_id=game_id, game__user=request.user)
        # Сохраняем ссылку на старый файл, чтобы удалить его после успешной транзакции
        if user_puzzle.user_image:
            old_puzzle_file_to_delete = user_puzzle.user_image
       
        # --- Парсинг FormData для PUT запросов ---
        # Настраиваем стандартные обработчики загрузки файлов для request.
        request.upload_handlers = [MemoryFileUploadHandler(request=request), TemporaryFileUploadHandler(request=request)]

        # Парсим тело запроса
        parser = MultiPartParser(request.META, BytesIO(request.body), request.upload_handlers)
        post_data, files_data = parser.parse()
        
        data = parse_and_validate_puzzle_data(post_data, files_data)
        
        current_has_preset = bool(user_puzzle.preset_image_path)
        current_has_user_image = bool(user_puzzle.user_image)
        
        with transaction.atomic():
            user_puzzle.name = data['name']
            user_puzzle.grid_size = data['grid_size']
            user_puzzle.piece_positions = data['piece_positions']
            
            if data['preset_path']:
                user_puzzle.user_image = None
                user_puzzle.preset_image_path = data['preset_path']
            elif data['uploaded_image_file']:
                user_puzzle.user_image = data['uploaded_image_file']
                user_puzzle.preset_image_path = None
            else:
                if not current_has_preset and not current_has_user_image:
                    return JsonResponse({'status': 'error', 'message': 'Ошибка: изображение не было предоставлено для обновления.'}, status=400)
            
            # Валидация модели и сохранение
            user_puzzle.full_clean()
            user_puzzle.save()
        
        if old_puzzle_file_to_delete and (data['preset_path'] or data['uploaded_image_file']):
            if default_storage.exists(old_puzzle_file_to_delete.name):
                old_puzzle_file_to_delete.delete(save=False)
        
        return JsonResponse({'status': 'success', 'message': f'Пазл "{data["name"]}" успешно обновлен!'})
        
    except ValueError as e:
        logger.warning(f"Ошибка валидации при обновлении пазла: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    except Http404:
        return JsonResponse({'status': 'error', 'message': 'Пазл для обновления не найден или у вас нет прав на его изменение.'}, status=404)
        
    except ValidationError as e:
        error_message = '; '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        logger.warning(f"Ошибка валидации модели при обновлении пазла: {e.message_dict}")
        return JsonResponse({'status': 'error', 'message': f'Ошибка введенных данных: {error_message}'}, status=400)
        
    except InternalError as e:
        return handle_db_integrity_error(e, 'puzzle', data.get('name', ''), f'и размером сетки {data.get("grid_size", 0)}x{data.get("grid_size", 0)}')
        
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при обновлении пазла (ID: {game_id}, User: {request.user.username}): {e.__class__.__name__}: {e}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при обновлении пазла. Попробуйте позже.'
        }, status=500)


@login_required
@require_POST
def save_memory_game_view(request):
    """
    Обрабатывает POST-запрос для сохранения состояния игры 'Поиск пар' для текущего пользователя.
    """
    custom_image_paths = []
    try:
        memory_genre = Genre.objects.get(code='MEM')
    except Genre.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ошибка конфигурации: Жанр "Поиск пар" не найден.'}, status=500)
    
    try:
        data = parse_and_validate_memory_game_data(request.POST, request.FILES)
        
        is_custom_set = bool(data['custom_images'])
        if not data['preset_name'] and not is_custom_set:
            return JsonResponse({'status': 'error', 'message': 'Необходимо выбрать пресет или загрузить изображения.'}, status=400)
        
        if is_custom_set:
            custom_image_paths = save_memory_game_custom_images(data['custom_images'], data['pair_count'])
        
        with transaction.atomic():
            new_game = UserGame.objects.create(user=request.user, genre=memory_genre)
            UserMemoryGame.objects.create(
                game=new_game,
                name=data['name'],
                pair_count=data['pair_count'],
                card_layout=data['card_layout'],
                preset_name=data['preset_name'],
                custom_image_paths=custom_image_paths if custom_image_paths else None
            )
        
        return JsonResponse({'status': 'success', 'message': f'Игра "{data["name"]}" успешно сохранена!', 'id': new_game.pk})
        
    except ValueError as e:
        cleanup_uploaded_files(custom_image_paths)
        logger.warning(f"Ошибка валидации при сохранении 'Поиска пар': {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    except InternalError as e:
        cleanup_uploaded_files(custom_image_paths)
        return handle_db_integrity_error(e, 'memory_game', data.get('name', ''), f'и количеством пар {data.get("pair_count", 0)}')
        
    except Exception as e:
        cleanup_uploaded_files(custom_image_paths)
        logger.error(f"Ошибка при сохранении 'Поиска пар': {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка.'}, status=500)


@login_required
@require_GET
def load_memory_games_view(request):
    """
    Обрабатывает GET-запрос для получения списка всех сохраненных игр 'Поиск пар' для текущего пользователя.
    """
    try:
        games = UserMemoryGame.objects.filter(game__user=request.user).select_related('game').order_by('-game__created_at')
        
        data_list = []
        for g in games:
            custom_image_urls = []
            if g.custom_image_paths:
                for path in g.custom_image_paths:
                    if default_storage.exists(path):
                        custom_image_urls.append(default_storage.url(path))
            
            data_list.append({
                'id': g.pk,
                'name': g.name,
                'pair_count': g.pair_count,
                'card_layout': g.card_layout,
                'preset_name': g.preset_name,
                'custom_image_urls': custom_image_urls if custom_image_urls else None,
            })
        return JsonResponse({'status': 'success', 'games': data_list})
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке 'Поиска пар': {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка при загрузке.'}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_memory_game_view(request, game_id: str):
    """
    Обрабатывает PUT-запрос для обновления существующей игры 'Поиск пар'.
    """
    new_paths = []
    old_paths_to_delete = []
    try:
        game_to_update = get_object_or_404(UserMemoryGame, pk=game_id, game__user=request.user)
        # Сохраняем копию списка старых путей, чтобы удалить их после успешной транзакции
        if game_to_update.custom_image_paths:
            old_paths_to_delete = list(game_to_update.custom_image_paths)

        # --- Парсинг FormData ---
        parser = MultiPartParser(request.META, BytesIO(request.body), request.upload_handlers)
        post_data, files_data = parser.parse()
        
        data = parse_and_validate_memory_game_data(post_data, files_data)
        
        if not data['preset_name'] and data['custom_images']:
            new_paths = save_memory_game_custom_images(data['custom_images'], data['pair_count'])
        
        with transaction.atomic():
            # Обновляем основные поля
            game_to_update.name = data['name']
            game_to_update.pair_count = data['pair_count']
            game_to_update.card_layout = data['card_layout']
            
            # Логика обновления изображений
            if data['preset_name']:
                game_to_update.custom_image_paths = None
                game_to_update.preset_name = data['preset_name']
            else:
                game_to_update.preset_name = None
                if new_paths:
                    game_to_update.custom_image_paths = new_paths
            
            game_to_update.save()
        
        if old_paths_to_delete and (data['preset_name'] or new_paths):
            cleanup_uploaded_files(old_paths_to_delete)
        
        return JsonResponse({'status': 'success', 'message': f'Игра "{data["name"]}" успешно обновлена!'})
        
    except ValueError as e:
        cleanup_uploaded_files(new_paths)
        logger.warning(f"Ошибка валидации при обновлении 'Поиска пар': {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    except Http404:
        cleanup_uploaded_files(new_paths)
        return JsonResponse({'status': 'error', 'message': 'Игра не найдена.'}, status=404)
        
    except InternalError as e:
        cleanup_uploaded_files(new_paths)
        return handle_db_integrity_error(e, 'memory_game', data.get('name', ''), f'и количеством пар {data.get("pair_count", 0)}')
        
    except Exception as e:
        cleanup_uploaded_files(new_paths)
        logger.error(f"Ошибка при обновлении 'Поиска пар' (ID: {game_id}): {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка при обновлении.'}, status=500)
    

@login_required
@require_POST
def save_sound_loto_view(request):
    """
    Обрабатывает POST-запрос для сохранения состояния игры 'Звуковое лото' для текущего пользователя.
    """
    custom_pairs = []
    try:
        sound_loto_genre = Genre.objects.get(code='SLT')
    except Genre.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ошибка конфигурации: Жанр "Звуковое лото" не найден.'}, status=500)
    
    try:
        data = parse_and_validate_sound_loto_data(request.POST, request.FILES)
        
        is_custom_set = bool(data['custom_images'])
        
        if is_custom_set:
            custom_pairs = save_sound_loto_custom_files(
                data['custom_images'],
                data['custom_audios'],
                data['custom_labels']
            )
            
        with transaction.atomic():
            new_game = UserGame.objects.create(user=request.user, genre=sound_loto_genre)
            UserSoundLoto.objects.create(
                game=new_game,
                name=data['name'],
                rounds_count=data['rounds_count'],
                cards_count=data['cards_count'],
                autoplay=data['autoplay'],
                show_labels=data['show_labels'],
                preset_name=data['preset_name'],
                custom_pairs=custom_pairs if custom_pairs else None
            )
        
        return JsonResponse({'status': 'success', 'message': f'Игра "{data["name"]}" успешно сохранена!', 'id': new_game.pk})
    
    except ValueError as e:
        cleanup_sound_loto_custom_files(custom_pairs)
        logger.warning(f"Ошибка валидации при сохранении 'Звукового лото': {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    except InternalError as e:
        cleanup_sound_loto_custom_files(custom_pairs)
        return handle_db_integrity_error(e, 'sound_loto', data.get('name', ''), f'и количеством раундов {data.get("rounds_count", 0)}')
        
    except Exception as e:
        cleanup_sound_loto_custom_files(custom_pairs)
        logger.error(f"Ошибка при сохранении 'Звукового лото': {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка.'}, status=500)


@login_required
@require_GET
def load_sound_lotos_view(request):
    """
    Обрабатывает GET-запрос для получения списка всех сохраненных игр 'Звуковое лото' для текущего пользователя.
    """
    try:
        games = UserSoundLoto.objects.filter(game__user=request.user).select_related('game').order_by('-game__created_at')
        
        data_list = []
        for g in games:
            custom_pairs_with_urls = []
            if g.custom_pairs:
                for pair in g.custom_pairs:
                    image_path = pair.get('image')
                    audio_path = pair.get('audio')
                    custom_pairs_with_urls.append({
                        'label': pair.get('label', ''),
                        'image_url': default_storage.url(image_path) if image_path and default_storage.exists(image_path) else None,
                        'audio_url': default_storage.url(audio_path) if audio_path and default_storage.exists(audio_path) else None,
                    })
                
            data_list.append({
                'id': g.pk,
                'name': g.name,
                'rounds_count': g.rounds_count,
                'cards_count': g.cards_count,
                'autoplay': g.autoplay,
                'show_labels': g.show_labels,
                'preset_name': g.preset_name,
                'custom_pairs': custom_pairs_with_urls if custom_pairs_with_urls else None,
            })
        return JsonResponse({'status': 'success', 'games': data_list})
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке 'Звукового лото': {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка при загрузке.'}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_sound_loto_view(request, game_id: str):
    """
    Обрабатывает PUT-запрос для обновления существующей игры 'Звуковое лото'.
    Поддерживает три сценария:
    1. Переключение на пресет.
    2. Загрузка новых файлов.
    3. Перестановка аудио и/или обновление подписей без пере-загрузки файлов.
    """
    new_pairs = []
    old_pairs_to_delete = []
    try:
        game_to_update = get_object_or_404(UserSoundLoto, pk=game_id, game__user=request.user)
        # Сохраняем копию старых пар для удаления после успешной транзакции
        if game_to_update.custom_pairs:
            old_pairs_to_delete = list(game_to_update.custom_pairs)
        
        # --- Парсинг FormData для PUT запросов ---
        request.upload_handlers = [MemoryFileUploadHandler(request=request), TemporaryFileUploadHandler(request=request)]
        parser = MultiPartParser(request.META, BytesIO(request.body), request.upload_handlers)
        post_data, files_data = parser.parse()

        data = parse_and_validate_sound_loto_data(post_data, files_data, is_update=True)

        is_custom_set = bool(data['custom_images'])

        if is_custom_set:
            new_pairs = save_sound_loto_custom_files(
                data['custom_images'],
                data['custom_audios'],
                data['custom_labels']
            )

        with transaction.atomic():
            # Обновляем основные поля
            game_to_update.name = data['name']
            game_to_update.rounds_count = data['rounds_count']
            game_to_update.cards_count = data['cards_count']
            game_to_update.autoplay = data['autoplay']
            game_to_update.show_labels = data['show_labels']

            # Логика обновления пар
            if data['preset_name']:
                # Сценарий 1: переключение на пресет
                game_to_update.custom_pairs = None
                game_to_update.preset_name = data['preset_name']
            elif new_pairs:
                # Сценарий 2: загружены новые файлы
                game_to_update.preset_name = None
                game_to_update.custom_pairs = new_pairs
            elif game_to_update.custom_pairs and (data.get('audio_order') or data.get('custom_labels')):
                # Сценарий 3: перестановка аудио и/или обновление подписей без пере-загрузки файлов
                game_to_update.preset_name = None
                updated_pairs = list(game_to_update.custom_pairs)

                if data.get('audio_order'):
                    audio_order = data['audio_order']
                    if len(audio_order) != len(updated_pairs):
                        raise ValueError("Порядок аудио не соответствует количеству пар.")
                    if sorted(audio_order) != list(range(len(updated_pairs))):
                        raise ValueError("Порядок аудио содержит некорректные или повторяющиеся индексы.")

                    # Извлекаем аудио в исходном порядке и переставляем по индексам
                    original_audios = [pair.get('audio') for pair in updated_pairs]
                    for i, source_idx in enumerate(audio_order):
                        updated_pairs[i]['audio'] = original_audios[source_idx]

                if data.get('custom_labels'):
                    labels = data['custom_labels']
                    if len(labels) == len(updated_pairs):
                        for i, label in enumerate(labels):
                            updated_pairs[i]['label'] = label

                game_to_update.custom_pairs = updated_pairs

            game_to_update.full_clean()
            game_to_update.save()

        # Удаляем старые файлы только при переключении на пресет или загрузке новых файлов
        if old_pairs_to_delete and (data['preset_name'] or new_pairs):
            cleanup_sound_loto_custom_files(old_pairs_to_delete)

        return JsonResponse({'status': 'success', 'message': f'Игра "{data["name"]}" успешно обновлена!'})

    except ValueError as e:
        cleanup_sound_loto_custom_files(new_pairs)
        logger.warning(f"Ошибка валидации при обновлении 'Звукового лото': {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    except ValidationError as e:
        cleanup_sound_loto_custom_files(new_pairs)
        error_message = '; '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        logger.warning(f"Ошибка валидации модели при обновлении 'Звукового лото': {e.message_dict}")
        return JsonResponse({'status': 'error', 'message': f'Ошибка введенных данных: {error_message}'}, status=400)

    except Http404:
        cleanup_sound_loto_custom_files(new_pairs)
        return JsonResponse({'status': 'error', 'message': 'Игра не найдена.'}, status=404)

    except InternalError as e:
        cleanup_sound_loto_custom_files(new_pairs)
        return handle_db_integrity_error(e, 'sound_loto', data.get('name', ''), f'и количеством раундов {data.get("rounds_count", 0)}')

    except Exception as e:
        cleanup_sound_loto_custom_files(new_pairs)
        logger.error(f"Ошибка при обновлении 'Звукового лото' (ID: {game_id}): {e}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'error', 'message': 'Произошла внутренняя ошибка при обновлении.'}, status=500)