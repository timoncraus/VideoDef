from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from account.models import User, Role, Gender


class AuthTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Тестовая роль")
        self.gender = Gender.objects.create(name="Мужской")

    def get_register_data(self):
        return {
            "username": "testuser",
            "email": "test@example.com",
            "phone_number": "+79991234567",
            "password1": "Testpassword123!",
            "password2": "Testpassword123!",
            "first_name": "Иван",
            "last_name": "Иванов",
            "patronymic": "Иванович",
            "date_birth": "2000-01-01",
            "role": self.role.id,
            "gender": self.gender.id,
            "photo": SimpleUploadedFile(
                "test.jpg", b"file_content", content_type="image/jpeg"
            ),
        }

    def test_login_success(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        user.phone_number = "+79991234567"
        user.save()
        response = self.client.post(
            reverse("account:login"),
            data={"identifier": "testuser", "password": "testpass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вы вошли в систему!")
