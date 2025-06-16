from django.core.management.base import BaseCommand

from account.models import User


class Command(BaseCommand):
    help = "Создание тестового суперпользователя"

    def handle(self, *args, **kwargs):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin123",
            )
            self.stdout.write(self.style.SUCCESS("Суперпользователь создан."))
        else:
            self.stdout.write("Суперпользователь уже существует.")
