from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Создание всех тестовых данных"

    def handle(self, *args, **kwargs):
        call_command("create_min")

        call_command("create_test_users")
        call_command("create_test_children")

        call_command("create_test_documents")
        call_command("create_test_resumes")

        call_command("create_test_chats")
        call_command("create_test_messages")

        self.stdout.write(self.style.SUCCESS("Все тестовые данные успешно созданы."))
