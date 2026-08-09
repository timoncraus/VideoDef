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
        url = f"/ws/puzzle_on_board/{board_room_name}/{game_id}/"
        
        communicator1 = WebsocketCommunicator(application, url)
        communicator2 = WebsocketCommunicator(application, url)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected1)
        self.assertTrue(connected2)

        test_message = json.dumps({"action": "move_piece", "piece": 1})
        
        # Первый отправляет сообщение
        await communicator1.send_to(text_data=test_message)

        # Второй получает (первый своё сообщение игнорирует)
        response = await communicator2.receive_from()
        self.assertEqual(response, test_message)

        await communicator1.disconnect()
        await communicator2.disconnect()


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
        url = f"/ws/whiteboard/{room_name}/"
        
        communicator1 = WebsocketCommunicator(application, url)
        communicator2 = WebsocketCommunicator(application, url)

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected1)
        self.assertTrue(connected2)

        test_message = json.dumps({"draw": "line", "points": [[0, 0], [1, 1]]})
        
        # Первый отправляет сообщение
        await communicator1.send_to(text_data=test_message)

        # Второй получает
        response = await communicator2.receive_from()
        self.assertEqual(response, test_message)

        await communicator1.disconnect()
        await communicator2.disconnect()