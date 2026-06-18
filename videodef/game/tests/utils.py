from django.test import TestCase
from django.contrib.auth import get_user_model
from game.models import Genre

User = get_user_model()


class GameTestBase(TestCase):
    """Базовый класс для тестов игр"""
    
    def setUp(self):
        super().setUp()
        
        # Создаем пользователя с коротким номером
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1234',
            phone_number='+7123456789'
        )
        
        # Создаем жанр
        self.genre = Genre.objects.create(
            code='PZL',
            name='Пазл'
        )