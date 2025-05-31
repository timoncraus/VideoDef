from django.test import TestCase

from chat.models import SmallChat, Message
from account.models import User, Profile, Role, Gender


class ChatTestBase(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Преподаватель")
        self.gender = Gender.objects.create(name="Мужской")

        profile1 = Profile.objects.create(
            first_name="Иван",
            last_name="Иванов",
            patronymic="Иванович",
            date_birth="1990-01-01",
            role=self.role,
            gender=self.gender
        )
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com",
                                              phone_number="+79991234567", password="pass1234", profile=profile1)

        profile2 = Profile.objects.create(
            first_name="Андрей",
            last_name="Иванов",
            patronymic="Николаевич",
            date_birth="1980-01-01",
            role=self.role,
            gender=self.gender
        )
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com",
                                              phone_number="+79991230000", password="pass1234", profile=profile2)
        self.chat = SmallChat.objects.create(user1=self.user1, user2=self.user2)
        self.message = Message.objects.create(chat=self.chat, sender=self.user1, content="Привет!")
