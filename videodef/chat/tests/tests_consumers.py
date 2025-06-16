from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from channels.routing import URLRouter
from django.urls import re_path

from chat.consumers import ChatConsumer
from chat.models import SmallChat

User = get_user_model()


class ChatConsumerTest(TransactionTestCase):
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
        self.chat = SmallChat.objects.create(user1=self.user1, user2=self.user2)

    async def test_connect_accept(self):
        application = URLRouter(
            [
                re_path(r"ws/chat/(?P<chat_id>\d+)/$", ChatConsumer.as_asgi()),
            ]
        )

        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.chat.id}/")
        communicator.scope["user"] = self.user1

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_connect_reject_anonymous(self):
        application = URLRouter(
            [
                re_path(r"ws/chat/(?P<chat_id>\d+)/$", ChatConsumer.as_asgi()),
            ]
        )

        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.chat.id}/")
        communicator.scope["user"] = type("AnonymousUser", (), {"is_anonymous": True})()

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_receive_message_and_broadcast(self):
        application = URLRouter(
            [
                re_path(r"ws/chat/(?P<chat_id>\d+)/$", ChatConsumer.as_asgi()),
            ]
        )

        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.chat.id}/")
        communicator.scope["user"] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_data = {"message": "Hello world"}
        await communicator.send_json_to(message_data)

        response = await communicator.receive_json_from()
        self.assertEqual(response["message"], "Hello world")
        self.assertEqual(response["message_type"], "sent")

        await communicator.disconnect()
