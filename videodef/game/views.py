from django.shortcuts import render

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