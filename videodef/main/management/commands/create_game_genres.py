from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Genre


class Command(BaseCommand):
    help = "Создание жанров игры"

    def handle(self, *args, **kwargs):
        genres = [
            (1, "Пазл", "PZL"),
        ]

        with transaction.atomic():
            Genre.objects.filter(id__in=[g[0] for g in genres]).delete()

            for gid, gname, gcode in genres:
                Genre.objects.create(id=gid, name=gname, code=gcode)

        self.stdout.write(self.style.SUCCESS("Жанры игры успешно созданы."))
