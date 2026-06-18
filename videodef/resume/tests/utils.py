from django.test import TestCase
from django.contrib.auth import get_user_model
from document.models import Document
from resume.models import ViolationType
import uuid

User = get_user_model()


class ResumeTestBase(TestCase):
    def setUp(self):
        super().setUp()
        # Используем короткий уникальный номер (не более 15 символов)
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            phone_number=f'+7{unique_id}'  # Короткий номер
        )
        self.client.login(username=self.user.username, password='testpass123')
        
        # Создаем тестовые данные
        self.document = Document.objects.create(
            user=self.user,
            name="Test Document",
            info="Test info"
        )
        self.violation = ViolationType.objects.create(
            name="Test Violation"
        )