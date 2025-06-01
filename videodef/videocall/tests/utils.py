from django.test import TestCase

from videocall.models import VideoCall
from account.models import User, Profile, Role, Gender


class VideoCallTestBase(TestCase):
    def setUp(self):
        self.role1 = Role.objects.create(name="Родитель")

        self.gender = Gender.objects.create(name="Мужской")

        profile1 = Profile.objects.create(
            first_name="Иван",
            last_name="Иванов",
            patronymic="Иванович",
            date_birth="1990-01-01",
            role=self.role1,
            gender=self.gender,
        )
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            phone_number="+79991234567",
            password="pass1234",
            profile=profile1,
        )

        self.role2 = Role.objects.create(name="Преподаватель")

        profile2 = Profile.objects.create(
            first_name="Андрей",
            last_name="Иванов",
            patronymic="Николаевич",
            date_birth="1980-01-01",
            role=self.role2,
            gender=self.gender,
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            phone_number="+79991230000",
            password="pass1234",
            profile=profile2,
        )

        self.call = VideoCall.objects.create(
            caller=self.user1, receiver=self.user2, room_name="testroom"
        )
