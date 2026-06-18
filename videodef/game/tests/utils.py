from django.test import TestCase
from django.contrib.auth import get_user_model
from game.models import Genre, UserGame

User = get_user_model()


class GameTestBase(TestCase):
    """Базовый класс для тестов игр"""
    
    def setUp(self):
        super().setUp()
        
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1234'
        )
        
        # Создаем жанр
        self.genre = Genre.objects.create(
            code='PZL',
            name='Пазл'
        )