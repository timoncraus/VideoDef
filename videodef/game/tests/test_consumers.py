import json

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.urls import re_path

from game.consumers import (
    PuzzleOnBoardConsumer,
    MemoryGameOnBoardConsumer,
    SoundLotoOnBoardConsumer,
    WhiteboardConsumer,
)


class GameOnBoardConsumerTestMixin:
    """Общий сценарий для игровых consumer'ов: подключение, обмен, отключение."""

    url_template = ""
    consumer = None

    async def _run(self, message):
        application = URLRouter([re_path(self.url_template, self.consumer.as_asgi())])
        url = self.url_template.replace("(?P<board_room_name>[\\w-]+)", "board1").replace("(?P<game_id>[\\w-]+)", "game1").replace("^", "").replace("$", "")
        c1 = WebsocketCommunicator(application, url)
        c2 = WebsocketCommunicator(application, url)
        connected1, _ = await c1.connect()
        connected2, _ = await c2.connect()
        assert connected1 and connected2

        await c1.send_to(text_data=message)
        self.assertEqual(await c2.receive_from(), message)

        await c1.disconnect()
        await c2.disconnect()


class PuzzleOnBoardConsumerTest(GameOnBoardConsumerTestMixin, TransactionTestCase):
    url_template = r"ws/puzzle_on_board/(?P<board_room_name>[\w-]+)/(?P<game_id>[\w-]+)/$"
    consumer = PuzzleOnBoardConsumer

    async def test_connect_receive_send_disconnect(self):
        await self._run(json.dumps({"action": "move_piece", "piece": 1}))


class MemoryGameOnBoardConsumerTest(GameOnBoardConsumerTestMixin, TransactionTestCase):
    url_template = r"ws/memory_game_on_board/(?P<board_room_name>[\w-]+)/(?P<game_id>[\w-]+)/$"
    consumer = MemoryGameOnBoardConsumer

    async def test_connect_receive_send_disconnect(self):
        await self._run(json.dumps({"type": "card_click", "cardDomIndex": 0}))


class SoundLotoOnBoardConsumerTest(GameOnBoardConsumerTestMixin, TransactionTestCase):
    url_template = r"ws/sound_loto_on_board/(?P<board_room_name>[\w-]+)/(?P<game_id>[\w-]+)/$"
    consumer = SoundLotoOnBoardConsumer

    async def test_connect_receive_send_disconnect(self):
        await self._run(json.dumps({"type": "card_click", "cardIndex": 0, "isCorrect": True}))


class WhiteboardConsumerTest(TransactionTestCase):
    async def test_connect_receive_send_disconnect(self):
        application = URLRouter([re_path(r"ws/whiteboard/(?P<room_name>[\w-]+)/$", WhiteboardConsumer.as_asgi())])
        c1 = WebsocketCommunicator(application, "/ws/whiteboard/room1/")
        c2 = WebsocketCommunicator(application, "/ws/whiteboard/room1/")
        connected1, _ = await c1.connect()
        connected2, _ = await c2.connect()
        self.assertTrue(connected1 and connected2)

        message = json.dumps({"draw": "line"})
        await c1.send_to(text_data=message)
        self.assertEqual(await c2.receive_from(), message)

        await c1.disconnect()
        await c2.disconnect()