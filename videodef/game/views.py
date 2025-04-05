from django.shortcuts import render

def games(request):
    dummy_games = [
        {"title": "Пазлы", "description": "Увлекательная игра, которая поможет развить внимание,\
          логику и пространственное восприятие. В этой игре вам предстоит собирать изображения, \
         разделенные на кусочки, и восстанавливать их в правильном порядке.", "image": "images/Game_Image.png"},
        {"title": "Игра 2", "description": "Описание игры 2", "image": "images/Game_Image.png"},
        {"title": "Игра 3", "description": "Описание игры 3", "image": "images/Game_Image.png"},
        {"title": "Игра 4", "description": "Описание игры 4", "image": "images/Game_Image.png"},
        {"title": "Игра 5", "description": "Описание игры 5", "image": "images/Game_Image.png"},
    ]
    return render(request, "game/game_main.html", {"games": dummy_games})

def puzzle_game(request):
    return render(request, "game/puzzles.html")