from django.test import TestCase
from django.contrib.auth import get_user_model
from document.models import Document
from resume.models import ViolationType

User = get_user_model()


class ResumeTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Создаем тестовые данные для документов и нарушений
        self.document = Document.objects.create(
            user=self.user,
            name="Test Document",
            info="Test info"
        )
        self.violation = ViolationType.objects.create(
            name="Test Violation"
        )