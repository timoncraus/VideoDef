from django.test import TestCase

from child.models import Child
from resume.models import ViolationType
from account.models import User, Gender


class ChildTestBase(TestCase):
    def setUp(self):
        self.gender = Gender.objects.create(name="Мужской")
        self.violation = ViolationType.objects.create(name="Аутизм")
        self.user = User.objects.create_user(
            username="parent",
            email="parent@example.com",
            password="pass123",
            phone_number="+79991234567",
        )
        self.client.login(username="parent", password="pass123")
        self.child = Child.objects.create(
            user=self.user,
            name="Петя",
            info="Информация",
            gender=self.gender,
            date_birth="2014-01-01",
        )
        self.child.violation_types.add(self.violation)
