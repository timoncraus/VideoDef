from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
from django.core.files import File
import os

from account.models import User, Profile, Role, Gender


class Command(BaseCommand):
    help = "Создание 4 тестовых пользователей с профилями"

    def handle(self, *args, **kwargs):
        try:
            gender_male = Gender.objects.get(name="Мужской")
            gender_female = Gender.objects.get(name="Женский")
            role_parent = Role.objects.get(name="Родитель")
            role_teacher = Role.objects.get(name="Преподаватель")

        except ObjectDoesNotExist as e:
            raise CommandError(f"Не найдены обязательные данные: {e}")

        base_dir = os.path.dirname(os.path.abspath(__file__))

        users_data = [
            {
                "username": "user1",
                "email": "user1@example.com",
                "phone_number": "+79000000001",
                "password": "pass1234",
                "first_name": "Ирина",
                "last_name": "Иванова",
                "patronymic": "Ивановна",
                "gender": gender_female,
                "role": role_parent,
                "date_birth": date(1990, 1, 1),
                "avatar_file": "photos/Ирина.jpg",
            },
            {
                "username": "user2",
                "email": "user2@example.com",
                "phone_number": "+79000000002",
                "password": "pass1234",
                "first_name": "Мария",
                "last_name": "Петрова",
                "patronymic": "Сергеевна",
                "gender": gender_female,
                "role": role_teacher,
                "date_birth": date(1992, 2, 2),
                "avatar_file": "photos/Мария.jpg",
            },
            {
                "username": "user3",
                "email": "user3@example.com",
                "phone_number": "+79000000003",
                "password": "pass1234",
                "first_name": "Алексей",
                "last_name": "Сидоров",
                "patronymic": "Алексеевич",
                "gender": gender_male,
                "role": role_teacher,
                "date_birth": date(1991, 3, 3),
                "avatar_file": "photos/Алексей.jpg",
            },
            {
                "username": "user4",
                "email": "user4@example.com",
                "phone_number": "+79000000004",
                "password": "pass1234",
                "first_name": "Елена",
                "last_name": "Кузнецова",
                "patronymic": "Николаевна",
                "gender": gender_female,
                "role": role_parent,
                "date_birth": date(1993, 4, 4),
                "avatar_file": "photos/Елена.jpg",
            },
        ]

        for user_data in users_data:
            username = user_data["username"]
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Пользователь {username} уже существует. Пропущен."
                    )
                )
                continue

            profile = Profile.objects.create(
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                patronymic=user_data["patronymic"],
                gender=user_data["gender"],
                role=user_data["role"],
                date_birth=user_data["date_birth"],
            )

            avatar_path = os.path.join(base_dir, user_data["avatar_file"])
            if os.path.exists(avatar_path):
                with open(avatar_path, "rb") as f:
                    profile.photo.save(user_data["avatar_file"], File(f), save=False)
            else:
                self.stdout.write(
                    self.style.WARNING(f"Аватар {user_data['avatar_file']} не найден.")
                )

            profile.save()

            User.objects.create_user(
                username=username,
                email=user_data["email"],
                password=user_data["password"],
                phone_number=user_data["phone_number"],
                profile=profile,
            )

            self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {username}"))
