from django.test import TestCase

from account.forms import RegisterForm, LoginForm
from account.models import Role, Gender


class FormTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Ученик")
        self.gender = Gender.objects.create(name="Женский")

    def test_register_form_valid(self):
        form = RegisterForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "phone_number": "+70001112233",
                "password1": "Strongpass123",
                "password2": "Strongpass123",
                "first_name": "Анна",
                "last_name": "Смирнова",
                "patronymic": "",
                "date_birth": "1999-12-12",
                "role": self.role.id,
                "gender": self.gender.id,
            }
        )
        self.assertTrue(form.is_valid())

    def test_login_form_invalid(self):
        form = LoginForm(data={"identifier": "", "password": ""})
        self.assertFalse(form.is_valid())
