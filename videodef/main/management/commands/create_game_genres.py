from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Genre

class Command(BaseCommand):
    help = "Создание жанров игры (безопасное, без удаления существующих)"

    def handle(self, *args, **kwargs):
        genres = [
            (1, "Пазл", "PZL"),
            (2, "Поиск пар", "MEM"),
            (3, "Звуковое лото", "SLT"),
        ]

        with transaction.atomic():
            for gid, gname, gcode in genres:
                obj, created = Genre.objects.update_or_create(
                    id=gid,
                    defaults={"name": gname, "code": gcode},
                )
                status = "создан" if created else "обновлен"
                self.stdout.write(f"  Жанр '{gname}' ({gcode}) {status}.")

        self.stdout.write(self.style.SUCCESS("Жанры игры успешно обработаны."))