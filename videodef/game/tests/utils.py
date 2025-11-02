from django.test import TestCase
from django.contrib.auth import get_user_model

from game.models import Genre

User = get_user_model()


class GameTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            phone_number="+79991234567",
            password="pass1234",
        )
        self.genre = Genre.objects.create(name="Пазл", code="PZL")
