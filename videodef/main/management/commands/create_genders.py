from django.core.management.base import BaseCommand
from django.db import transaction

from account.models import Gender


class Command(BaseCommand):
    help = "Создание полов"

    def handle(self, *args, **kwargs):
        genders = [
            (1, "Мужской"),
            (2, "Женский"),
        ]

        with transaction.atomic():
            Gender.objects.filter(id__in=[g[0] for g in genders]).delete()

            for gid, gname in genders:
                Gender.objects.create(id=gid, name=gname)

        self.stdout.write(self.style.SUCCESS("Полы успешно созданы."))
