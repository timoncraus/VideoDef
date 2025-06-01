from django.core.management.base import BaseCommand
from django.db import transaction

from account.models import Role


class Command(BaseCommand):
    help = "Создание ролей"

    def handle(self, *args, **kwargs):
        roles = [
            (1, "Родитель"),
            (2, "Преподаватель"),
        ]

        with transaction.atomic():
            Role.objects.filter(id__in=[r[0] for r in roles]).delete()

            for rid, rname in roles:
                Role.objects.create(id=rid, name=rname)

        self.stdout.write(self.style.SUCCESS("Роли успешно созданы."))
