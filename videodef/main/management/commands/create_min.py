from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Создание минимальных данных"

    def handle(self, *args, **kwargs):
        call_command("create_roles")
        call_command("create_genders")
        call_command("create_admin_user")

        call_command("create_violation_types")

        call_command("create_game_genres")

        self.stdout.write(self.style.SUCCESS("Минимальные данные успешно созданы."))
