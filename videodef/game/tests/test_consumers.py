import json
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path

from game.consumers import PuzzleOnBoardConsumer, WhiteboardConsumer


class PuzzleOnBoardConsumerTest(TransactionTestCase):
    async def test_connect_receive_send_disconnect(self):
        application = URLRouter(
            [
                re_path(
                    r"ws/puzzle_on_board/(?P<board_room_name>[\w-]+)/(?P<game_id>[\w-]+)/$",
                    PuzzleOnBoardConsumer.as_asgi(),
                ),
            ]
        )

        board_room_name = "board123"
        game_id = "game456"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/puzzle_on_board/{board_room_name}/{game_id}/",
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        test_message = json.dumps({"action": "move_piece", "piece": 1})
        await communicator.send_to(text_data=test_message)

        response = await communicator.receive_from()
        self.assertEqual(response, test_message)

        await communicator.disconnect()


class WhiteboardConsumerTest(TransactionTestCase):
    async def test_connect_receive_send_disconnect(self):
        application = URLRouter(
            [
                re_path(
                    r"ws/whiteboard/(?P<room_name>[\w-]+)/$",
                    WhiteboardConsumer.as_asgi(),
                ),
            ]
        )

        room_name = "room123"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/whiteboard/{room_name}/",
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        test_message = json.dumps({"draw": "line", "points": [[0, 0], [1, 1]]})
        await communicator.send_to(text_data=test_message)

        response = await communicator.receive_from()
        self.assertEqual(response, test_message)

        await communicator.disconnect()
