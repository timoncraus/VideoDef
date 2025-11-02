from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from account.models import User
from chat.models import SmallChat


class Command(BaseCommand):
    help = "Создание тестовых чатов между родителями и преподавателями"

    def handle(self, *args, **kwargs):
        try:
            user1 = User.objects.get(username="user1")  # Ирина (Родитель)
            user2 = User.objects.get(username="user2")  # Мария (Преподаватель)
            user3 = User.objects.get(username="user3")  # Алексей (Преподаватель)
            user4 = User.objects.get(username="user4")  # Елена (Родитель)

        except ObjectDoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
            return

        chats_data = [
            {"user1": user1, "user2": user2},  # Ирина <-> Мария
            {"user1": user1, "user2": user3},  # Ирина <-> Алексей
            {"user1": user4, "user2": user2},  # Елена <-> Мария
            {"user1": user4, "user2": user3},  # Елена <-> Алексей
        ]

        for chat in chats_data:
            u1 = chat["user1"]
            u2 = chat["user2"]

            if (
                SmallChat.objects.filter(user1=u1, user2=u2).exists()
                or SmallChat.objects.filter(user1=u2, user2=u1).exists()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"Чат между {u1.username} и {u2.username} уже существует"
                    )
                )
                continue

            SmallChat.objects.create(user1=u1, user2=u2)
            self.stdout.write(
                self.style.SUCCESS(f"Создан чат между {u1.username} и {u2.username}")
            )
