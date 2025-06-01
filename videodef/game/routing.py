from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/puzzle_on_board/(?P<board_room_name>[\w-]+)/(?P<game_id>[\w-]+)/$",
        consumers.PuzzleOnBoardConsumer.as_asgi(),
    ),
    re_path(
        r"ws/whiteboard/(?P<room_name>[\w-]+)/$", consumers.WhiteboardConsumer.as_asgi()
    ),
]
