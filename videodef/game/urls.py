from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    path("", views.games, name="games"),
    path("whiteboard/", views.whiteboard, name="whiteboard"),
    path("puzzle/", views.puzzle_game, name="puzzle_game"),
    path("memory/", views.memory_game, name="memory_game"),
    path("sound-loto/", views.sound_loto, name="sound_loto"),
    path("my-games/", views.my_games_view, name="my_games"),
    path("api/save-puzzle/", views.save_puzzle_view, name="save_puzzle"),
    path("api/load-puzzles/", views.load_puzzles_view, name="load_puzzles"),
    path("api/update-puzzle/<str:game_id>/", views.update_puzzle_view, name="update_puzzle"),
    path("api/save-memory-game/", views.save_memory_game_view, name="save_memory_game"),
    path("api/load-memory-games/", views.load_memory_games_view, name="load_memory_games"),
    path("api/update-memory-game/<str:game_id>/", views.update_memory_game_view, name="update_memory_game"),
    path("api/save-sound-loto/", views.save_sound_loto_view, name="save_sound_loto"),
    path("api/load-sound-lotos/", views.load_sound_lotos_view, name="load_sound_lotos"),
    path("api/update-sound-loto/<str:game_id>/", views.update_sound_loto_view, name="update_sound_loto"),
    path("api/delete-game/<str:game_id>/", views.delete_game_view, name="delete_game"),
]