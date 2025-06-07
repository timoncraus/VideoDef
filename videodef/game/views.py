from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction, InternalError
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.http.multipartparser import MultiPartParser
from django.conf import settings
from django.templatetags.static import static
from django.db.models import Value, CharField, OuterRef, Subquery, F
from django.db.models.functions import Concat, Coalesce
from io import BytesIO
from .models import UserGame, UserPuzzle, Genre
import json
import traceback

def games(request):
    games = [
        {"title": "Интерактивная доска",\
         "description": "Интерактивная доска для совместного рисования и работы с изображениями \
          в реальном времени. Поддерживает многопользовательский режим, перетаскивание и масштабирование картинок.",\
         "image": "images/board.png",\
         "url": "whiteboard"},
        {"title": "Пазлы",\
         "description": "Увлекательная игра, которая поможет развить внимание,\
          логику и пространственное восприятие. В этой игре вам предстоит собирать изображения, \
          разделенные на кусочки, и восстанавливать их в правильном порядке.",\
          "image": "images/Puzzle_game.png",\
          "url": "puzzle_game"},
        {"title": "Поиск пар",\
         "description": "Классическая игра на развитие памяти и концентрации. Открывайте карточки, запоминайте расположение уникальных изображений и находите совпадающие пары.",\
         "image": "images/Memory_game.png",\
         "url": "memory_game"},
    ]
    return render(request, "game/game_main.html", {"games": games})

def puzzle_game(request):
    return render(request, "game/puzzles.html")

def memory_game(request):
    return render(request, "game/memory-game.html")

def whiteboard(request):
    return render(request, "game/whiteboard.html")

@login_required
def my_games_view(request):
    """
    Отображает страницу со списком всех сохраненных игр текущего пользователя
    """
    
    # --- Получение базового запроса с аннотацией display_name ---
    puzzle_name_subquery = UserPuzzle.objects.filter(
        game_id=OuterRef('pk')
    ).values('name')[:1]

    user_games_query = UserGame.objects.filter(user=request.user)\
    .select_related('genre').annotate(
        display_name=Coalesce(
            Subquery(puzzle_name_subquery, output_field=CharField(null=True)),
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

    valid_sort_fields = {
        'name': 'display_name',
        'genre': 'genre__name',
        'created': 'created_at',
        'updated': 'updated_at'
    }
    
    sort_field_db = valid_sort_fields.get(sort_by_param, 'created_at')

    if sort_order_param == 'desc':
        user_games_query = user_games_query.order_by(F(sort_field_db).desc(nulls_last=True))
    else:
        user_games_query = user_games_query.order_by(F(sort_field_db).asc(nulls_last=True))

    # Выполняем запрос
    user_games_list = list(user_games_query)

    # --- Добавление URL изображений для пазлов ---
    puzzle_game_pks = [game.pk for game in user_games_list if game.genre.code == 'PZL']
    puzzle_details_map = {}
    if puzzle_game_pks:
        puzzles_data = UserPuzzle.objects.filter(game_id__in=puzzle_game_pks)\
        .only('game_id', 'preset_image_path', 'user_image')
        for p_data in puzzles_data:
            puzzle_details_map[p_data.game_id] = p_data.image_url

    for game_obj in user_games_list:
        if game_obj.genre.code == 'PZL':
            game_obj.display_image_url = puzzle_details_map.get(game_obj.pk)
        else:
            game_obj.display_image_url = None


    context = {
        'user_games': user_games_list,
        'genres_for_filter': genres_for_filter,
        'current_filters': {
            'genre': selected_genre_id,
        },
        'current_sort': {
            'by': sort_by_param,
            'order': sort_order_param,
        }
    }
    return render(request, "game/my_games.html", context)

@login_required
@require_http_methods(["DELETE"])
def delete_game_view(request, game_id):
    """
    Удаляет игру с указанным game_id, принадлежащую текущему пользователю.
    """
    try:
        game_to_delete = get_object_or_404(UserGame, pk=game_id, user=request.user)
        
        game_name_display = game_to_delete.game_id
        
        if game_to_delete.genre and game_to_delete.genre.code == 'PZL':
            try:
                if hasattr(game_to_delete, 'puzzle_details') and game_to_delete.puzzle_details:
                    game_name_display = game_to_delete.puzzle_details.name
            except UserPuzzle.DoesNotExist:
                pass

        game_to_delete.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Игра "{game_name_display}" успешно удалена.'
        })

    except UserGame.DoesNotExist: 
        return JsonResponse({'status': 'error', 'message': 'Игра не найдена или у вас нет прав на её удаление.'}, status=404)
    except Exception as e:
        print(f"Ошибка при удалении игры {game_id} для пользователя {request.user.username}: {e}")
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': 'Произошла ошибка при удалении игры.'}, status=500)

@login_required
@require_POST
def save_puzzle_view(request):
    """
    Обрабатывает POST-запрос для сохранения состояния игры-пазла для текущего пользователя.
    Ожидает данные в формате FormData (из request.POST и request.FILES).
    Создает записи в UserGame и UserPuzzle.
    """

    name = ""
    grid_size = 0

    # --- Получение жанра "Пазл" ---
    try:
        puzzle_genre = Genre.objects.get(code='PZL')
    except Genre.DoesNotExist:
        print("КРИТИЧЕСКАЯ ОШИБКА: Жанр 'Пазл' (код PZL) не найден в базе данных!")
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка конфигурации сервера: Жанр пазлов отсутствует в базе данных'
        }, status=500)
    
    try:
        # --- Извлечение данных из FormData ---
        name = request.POST.get('name', '').strip()
        grid_size_str = request.POST.get('gridSize')
        piece_positions_str = request.POST.get('piecePositions')
        preset_path = request.POST.get('preset_image_path')
        uploaded_image_file = request.FILES.get('user_image_file')

        # --- Валидация входных данных ---
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Название не может быть пустым.'}, status=400)

        # Валидация размера сетки
        try:
            grid_size = int(grid_size_str)
            if grid_size < 2:
                raise ValueError("Размер сетки слишком мал.")
        except (TypeError, ValueError, KeyError):
             return JsonResponse({'status': 'error', 'message': 'Неверный или отсутствующий размер сетки.'}, status=400)

        # Валидация позиций элементов
        try:
            if not piece_positions_str:
                 raise ValueError("Данные о позициях элементов отсутствуют.")
            piece_positions = json.loads(piece_positions_str)
            if not isinstance(piece_positions, list) or not all(isinstance(p, int) for p in piece_positions):
                 raise ValueError("Позиции должны быть списком целых чисел.")
            expected_length = grid_size * grid_size
            if len(piece_positions) != expected_length:
                 raise ValueError(f"Количество позиций ({len(piece_positions)}) не соответствует размеру сетки ({expected_length}).")
        except (TypeError, ValueError, json.JSONDecodeError) as e:
             print(f"Ошибка парсинга/валидации позиций: {e}, получено: '{piece_positions_str}'")
             return JsonResponse({'status': 'error', 'message': f'Неверный формат или содержимое позиций элементов: {e}'}, status=400)
        except KeyError:
             return JsonResponse({'status': 'error', 'message': 'Данные о позициях элементов не переданы.'}, status=400)

        # Проверка источника изображения (должен быть указан только один)
        if preset_path and uploaded_image_file:
             return JsonResponse({'status': 'error', 'message': 'Нельзя одновременно указать пресет и загрузить файл.'}, status=400)
        if not preset_path and not uploaded_image_file:
             return JsonResponse({'status': 'error', 'message': 'Необходимо выбрать пресет или загрузить изображение.'}, status=400)

        # --- Создание записей в Базе Данных ---
        with transaction.atomic():
            new_game = UserGame(
                user=request.user,
                genre=puzzle_genre
            )
            new_game.save()

            puzzle = UserPuzzle(
                game=new_game,
                name=name,
                grid_size=grid_size,
                piece_positions=piece_positions,
                preset_image_path=preset_path if preset_path else None,
                user_image=uploaded_image_file if uploaded_image_file else None
            )

            puzzle.full_clean()
            puzzle.save()

        return JsonResponse({'status': 'success', 'message': f'Пазл "{name}" успешно сохранен!'})

    # --- Обработка ошибок ---
    except ValidationError as e:
        error_message = '; '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        print(f"Ошибка валидации при сохранении пазла: {e.message_dict}")
        return JsonResponse({'status': 'error', 'message': f'Ошибка введенных данных: {error_message}'}, status=400)
    except InternalError as e:
        db_error_message = str(e).lower()
        # Проверяем, содержит ли сообщение текст из RAISE EXCEPTION триггера
        trigger_error_text_part1 = 'пазл с названием'
        trigger_error_text_part2 = 'уже существует'

        if trigger_error_text_part1 in db_error_message and trigger_error_text_part2 in db_error_message:
            # Формируем сообщение на основе данных, которые пытались сохранить
            error_detail = f'Пазл с названием "{name}" и размером сетки {grid_size}x{grid_size} уже существует.'
            print(f"Ошибка уникальности пазла: {error_detail} | Оригинальная ошибка: {e}")
            return JsonResponse({'status': 'error', 'message': error_detail}, status=400)
        else:
            print(f"Непредвиденная ошибка целостности БД при сохранении пазла ({request.user.username}): {e.__class__.__name__}: {e}")
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': 'Произошла ошибка базы данных при сохранении пазла. Попробуйте позже.'
            }, status=500)
    except Exception as e:
        print(f"Непредвиденная ошибка при сохранении пазла ({request.user.username}): {e.__class__.__name__}: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при сохранении пазла. Попробуйте позже.'
        }, status=500)

@login_required
@require_GET
def load_puzzles_view(request):
    """
    Обрабатывает GET-запрос для получения списка всех сохраненных пазлов
    для текущего пользователя. Возвращает полный набор данных для каждого пазла
    """
    # --- Получение жанра "Пазл" ---
    try:
        puzzle_genre = Genre.objects.get(code='PZL')
    except Genre.DoesNotExist:
        print("КРИТИЧЕСКАЯ ОШИБКА: Жанр 'Пазл' (код PZL) не найден в базе данных!")
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

    # --- Обработка ошибок ---
    except Exception as e:
        print(f"Ошибка при загрузке списка пазлов ({request.user.username}): {e.__class__.__name__}: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при загрузке списка пазлов.'
        }, status=500)
    

@login_required
@require_http_methods(["PUT"])
@transaction.atomic
def update_puzzle_view(request, game_id):
    """
    Обрабатывает PUT-запрос для обновления существующего пазла.
    Данные ожидает в FormData.
    """
    try:
        user_puzzle = get_object_or_404(UserPuzzle, game_id=game_id, game__user=request.user)
       
        # --- Парсинг FormData для PUT запросов ---
        # Настраиваем стандартные обработчики загрузки файлов для request.
        request.upload_handlers = [MemoryFileUploadHandler(request=request), TemporaryFileUploadHandler(request=request)]

        # Парсим тело запроса
        parser = MultiPartParser(request.META, BytesIO(request.body), request.upload_handlers)
        post_data, files_data = parser.parse()
        
        # --- Извлечение данных из распарсенных данных ---
        name = post_data.get('name', '').strip()
        grid_size_str = post_data.get('gridSize')
        piece_positions_str = post_data.get('piecePositions')
        preset_path = post_data.get('preset_image_path')
        uploaded_image_file = files_data.get('user_image_file')

        # --- Валидация входных данных ---
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Название не может быть пустым.'}, status=400)

        try:
            grid_size = int(grid_size_str)
            if grid_size < 2:
                raise ValueError("Размер сетки слишком мал.")
        except (TypeError, ValueError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Неверный или отсутствующий размер сетки.'}, status=400)

        try:
            if not piece_positions_str:
                raise ValueError("Данные о позициях элементов отсутствуют.")
            piece_positions = json.loads(piece_positions_str)
            if not isinstance(piece_positions, list) or not all(isinstance(p, int) for p in piece_positions):
                raise ValueError("Позиции должны быть списком целых чисел.")
            expected_length = grid_size * grid_size
            if len(piece_positions) != expected_length:
                raise ValueError(f"Количество позиций ({len(piece_positions)}) не соответствует размеру сетки ({expected_length}).")
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Ошибка парсинга/валидации позиций при обновлении: {e}, получено: '{piece_positions_str}'")
            return JsonResponse({'status': 'error', 'message': f'Неверный формат или содержимое позиций элементов: {e}'}, status=400)
        except KeyError:
            return JsonResponse({'status': 'error', 'message': 'Данные о позициях элементов не переданы.'}, status=400)

        # Проверка источника изображения
        current_has_preset = bool(user_puzzle.preset_image_path)
        current_has_user_image = bool(user_puzzle.user_image)

        # --- Обновление полей UserPuzzle ---
        user_puzzle.name = name
        user_puzzle.grid_size = grid_size
        user_puzzle.piece_positions = piece_positions

        # Логика обновления изображения
        if preset_path: # Пользователь выбрал/оставил пресет
            if user_puzzle.user_image:
                user_puzzle.user_image.delete(save=False)
                user_puzzle.user_image = None
            user_puzzle.preset_image_path = preset_path
        elif uploaded_image_file: # Пользователь загрузил новый файл
            if user_puzzle.user_image:
                user_puzzle.user_image.delete(save=False)
            user_puzzle.user_image = uploaded_image_file
            user_puzzle.preset_image_path = None
        else:
              if not current_has_preset and not current_has_user_image:
                  return JsonResponse({'status': 'error', 'message': 'Ошибка: изображение не было предоставлено для обновления.'}, status=400)

        # Валидация модели и сохранение
        user_puzzle.full_clean()
        user_puzzle.save()

        return JsonResponse({'status': 'success', 'message': f'Пазл "{name}" успешно обновлен!'})

    # Обработка возможных ошибок
    except UserPuzzle.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Пазл для обновления не найден или у вас нет прав на его изменение.'}, status=404)
    except ValidationError as e:
        error_message = '; '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        print(f"Ошибка валидации при обновлении пазла: {e.message_dict}")
        return JsonResponse({'status': 'error', 'message': f'Ошибка введенных данных: {error_message}'}, status=400)
    except Exception as e:
        print(f"Непредвиденная ошибка при обновлении пазла (ID: {game_id}, User: {request.user.username}): {e.__class__.__name__}: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': 'Произошла внутренняя ошибка сервера при обновлении пазла. Попробуйте позже.'
        }, status=500)