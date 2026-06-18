from django.test import TestCase
from django.contrib.auth import get_user_model
from document.models import Document
from resume.models import ViolationType
from account.models import Profile, Role, Gender
import uuid

User = get_user_model()


class ResumeTestBase(TestCase):
    def setUp(self):
        super().setUp()
        
        # Создаем роли если их нет
        self.parent_role, _ = Role.objects.get_or_create(name="Родитель")
        self.teacher_role, _ = Role.objects.get_or_create(name="Преподаватель")
        self.gender, _ = Gender.objects.get_or_create(name="Мужской")
        
        # Создаем пользователя
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            phone_number=f'+7{unique_id[:10]}'
        )
        
        # Создаем профиль
        self.profile = Profile.objects.create(
            user=self.user,
            role=self.parent_role,
            gender=self.gender,
            first_name="Новый",
            last_name="Пользователь",
            patronymic="Тестович",
            date_birth="2000-01-01",
            max_search_distance=10,
        )
        
        # Убеждаемся, что профиль привязан к пользователю
        self.user.profile = self.profile
        self.user.save()
        
        # Логинимся через клиент
        login_success = self.client.login(username=self.user.username, password='testpass123')
        if not login_success:
            # Если не получается, пробуем через force_login
            self.client.force_login(self.user)
        
        # Создаем тестовые данные
        self.document = Document.objects.create(
            user=self.user,
            name="Test Document",
            info="Test info"
        )
        self.violation = ViolationType.objects.create(
            name="Test Violation"
        )