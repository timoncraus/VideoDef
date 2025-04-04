from django.shortcuts import render

def games(request):
    dummy_games = [
        {"title": "Игра 1", "description": "Описание игры 1", "image": "images/Game_Image.png"},
        {"title": "Игра 2", "description": "Описание игры 2", "image": "images/Game_Image.png"},
        {"title": "Игра 3", "description": "Описание игры 3", "image": "images/Game_Image.png"},
        {"title": "Игра 4", "description": "Описание игры 4", "image": "images/Game_Image.png"},
        {"title": "Игра 5", "description": "Описание игры 5", "image": "images/Game_Image.png"},
    ]
    return render(request, "game/game_main.html", {"games": dummy_games})
