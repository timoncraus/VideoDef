from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    path("", views.games, name="games"),
    path("my/", views.my_games_view, name="my_games"),
    path("puzzles/", views.puzzle_game, name="puzzle_game"),
    path("whiteboard/", views.whiteboard, name="whiteboard"),
    path("puzzles/save/", views.save_puzzle_view, name="save_puzzle"),
    path("puzzles/load/", views.load_puzzles_view, name="load_puzzles"),
    path(
        "puzzles/update/<str:game_id>/", views.update_puzzle_view, name="update_puzzle"
    ),
    path("delete/<str:game_id>/", views.delete_game_view, name="delete_game"),
]
