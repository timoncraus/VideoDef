from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from videocall.tests.utils import VideoCallTestBase
from account.models import Profile

User = get_user_model()


class VideoCallViewTest(VideoCallTestBase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_videocall_view_renders(self):
        response = self.client.get(reverse('videocall:videocall', args=['room123']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'videocall/videocall.html')

    def test_start_call_requires_login(self):
        response = self.client.post(reverse('videocall:start_call'), content_type='application/json', data=json.dumps({
            'receiver_id': self.user2.unique_id
        }))
        self.assertEqual(response.status_code, 302)

    def test_start_call_success(self):
        self.client.login(username="user1", password="pass1234")
        response = self.client.post(reverse('videocall:start_call'), content_type='application/json', data=json.dumps({
            'receiver_id': self.user2.unique_id
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIn('room_name', response.json())
