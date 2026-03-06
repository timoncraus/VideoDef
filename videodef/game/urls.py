from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    path("", views.games, name="games"),
    path("whiteboard/", views.whiteboard, name="whiteboard"),
    path("puzzle/", views.puzzle_game, name="puzzle_game"),
    path("memory/", views.memory_game, name="memory_game"),
    path("my-games/", views.my_games_view, name="my_games"),
    path("api/save-puzzle/", views.save_puzzle_view, name="save_puzzle"),
    path("api/load-puzzles/", views.load_puzzles_view, name="load_puzzles"),
    path("api/update-puzzle/<int:game_id>/", views.update_puzzle_view, name="update_puzzle"),
    path("api/save-memory-game/", views.save_memory_game_view, name="save_memory_game"),
    path("api/load-memory-games/", views.load_memory_games_view, name="load_memory_games"),
    path("api/update-memory-game/<int:game_id>/", views.update_memory_game_view, name="update_memory_game"),
    path("api/delete-game/<int:game_id>/", views.delete_game_view, name="delete_game"),
]