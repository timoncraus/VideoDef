from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from channels.routing import URLRouter
from django.urls import re_path
import uuid
import asyncio

from videocall.consumers import VideoCallConsumer
from videocall.models import VideoCall

User = get_user_model()

class VideoCallConsumerTest(TransactionTestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com",
                                              phone_number="+79991234567", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com",
                                              phone_number="+79991230000", password="pass1234")
        self.call = VideoCall.objects.create(caller=self.user1, receiver=self.user2, room_name="testroom")

    async def test_connect_accept(self):
        application = URLRouter([
            re_path(r'ws/videocall/(?P<room_name>\w+)/$', VideoCallConsumer.as_asgi()),
        ])

        communicator = WebsocketCommunicator(application, f"/ws/videocall/{self.call.room_name}/")
        communicator.scope['user'] = self.user1

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()
