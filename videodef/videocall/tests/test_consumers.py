from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
import asyncio

from videocall.consumers import VideoCallConsumer
from videocall.models import VideoCall

User = get_user_model()

application = URLRouter(
    [
        re_path(r"ws/videocall/(?P<room_name>\w+)/$", VideoCallConsumer.as_asgi()),
    ]
)


class VideoCallConsumerTest(TransactionTestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            phone_number="+79991234567",
            password="pass1234",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            phone_number="+79991230000",
            password="pass1234",
        )
        self.call = VideoCall.objects.create(
            caller=self.user1, receiver=self.user2, room_name="testroom"
        )

    async def test_connection_as_participant(self):
        communicator = WebsocketCommunicator(application, "/ws/videocall/testroom/")
        communicator.scope["user"] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "role")
        self.assertTrue(response["initiator"])

        await communicator.disconnect()

    async def test_connection_as_non_participant_should_close(self):
        stranger = await sync_to_async(User.objects.create_user)(
            username="stranger",
            email="stranger@example.com",
            phone_number="+79991239999",
            password="pass1234",
        )

        communicator = WebsocketCommunicator(application, "/ws/videocall/testroom/")
        communicator.scope["user"] = stranger
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_receive_end_call(self):
        communicator = WebsocketCommunicator(application, "/ws/videocall/testroom/")
        communicator.scope["user"] = self.user1
        await communicator.connect()

        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "end_call"})
        await asyncio.sleep(0.1)

        call = await sync_to_async(VideoCall.objects.get)(room_name="testroom")
        self.assertIsNotNone(call.ended_at)

        await communicator.disconnect()

    async def test_disconnect_should_set_ended_at_if_last(self):
        communicator = WebsocketCommunicator(application, "/ws/videocall/testroom/")
        communicator.scope["user"] = self.user1
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.disconnect()
        await asyncio.sleep(0.1)

        call = await sync_to_async(VideoCall.objects.get)(room_name="testroom")
        self.assertIsNotNone(call.ended_at)
