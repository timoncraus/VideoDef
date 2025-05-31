
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from unittest.mock import patch

from chat.tests.utils import ChatTestBase
from account.models import User
from chat.models import SmallChat, Message
from videocall.models import VideoCall


class ChatViewsTest(ChatTestBase):
    def test_chats_view_authenticated(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('chat:chats'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('chats_info', response.context)
        self.assertContains(response, "Привет!")

    def test_chat_room_access_allowed(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('chat:chat_room', args=[self.chat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('events', response.context)

    def test_chat_room_access_forbidden(self):
        other_user = User.objects.create_user(username='user3', password='pass',
                                              email="user3@example.com",
                                              phone_number="+79991233333")
        self.client.force_login(other_user)
        response = self.client.get(reverse('chat:chat_room', args=[self.chat.id]))
        self.assertEqual(response.status_code, 403)

    def test_get_chat_existing(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('chat:get_chat', args=[self.user1.unique_id, self.user2.unique_id]))
        self.assertRedirects(response, reverse('chat:chat_room', args=[self.chat.id]))

    def test_get_chat_new(self):
        self.client.force_login(self.user1)
        new_user = User.objects.create_user(username='user4', password='pass',
                                            email="user4@example.com",
                                            phone_number="+79991234444")
        response = self.client.get(reverse('chat:get_chat', args=[self.user1.unique_id, new_user.unique_id]))
        new_chat = SmallChat.objects.filter(user1=self.user1, user2=new_user).first()
        self.assertIsNotNone(new_chat)
        self.assertRedirects(response, reverse('chat:chat_room', args=[new_chat.id]))

    def test_get_chat_same_user_redirect(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('chat:get_chat', args=[self.user1.unique_id, self.user1.unique_id]))
        self.assertRedirects(response, reverse('chat:chats'))
