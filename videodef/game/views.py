from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.core.exceptions import ValidationError
from django.db import transaction, InternalError
from django.conf import settings
from django.templatetags.static import static
from .models import UserGame, UserPuzzle, Genre
import json
import traceback

def games(request):
    dummy_games = [
        {"title": "Интерактивная доска", "description": "Интерактивная доска для совместного рисования и работы с изображениями \
          в реальном времени. Поддерживает многопользовательский режим, перетаскивание и масштабирование картинок.", \
          "image": "images/board.png",\
         "url": "whiteboard"},
        {"title": "Пазлы", "description": "Увлекательная игра, которая поможет развить внимание,\
          логику и пространственное восприятие. В этой игре вам предстоит собирать изображения, \
          разделенные на кусочки, и восстанавливать их в правильном порядке.", "image": "images/Game_Image.png", \
            "url": "puzzle_game"},
        {"title": "Игра 3", "description": "Описание игры 3", "image": "images/Game_Image.png",\
         "url": "#"},
        {"title": "Игра 4", "description": "Описание игры 4", "image": "images/Game_Image.png",\
         "url": "#"},
        {"title": "Игра 5", "description": "Описание игры 5", "image": "images/Game_Image.png",\
         "url": "#"},
    ]
    return render(request, "game/game_main.html", {"games": dummy_games})

def puzzle_game(request):
    return render(request, "game/puzzles.html")

def whiteboard(request):
    return render(request, "game/whiteboard.html")

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