from django.core.management.base import BaseCommand
from django.db import transaction

from resume.models import ViolationType


class Command(BaseCommand):
    help = "Создание видов нарушений"

    def handle(self, *args, **kwargs):
        violations = [
            (1, "Дети с нарушением слуха (глухие, слабослышащие, позднооглохшие)"),
            (2, "Дети с нарушением зрения (слепые, слабовидящие)"),
            (3, "Дети с нарушением речи (логопаты)"),
            (4, "Дети с нарушением опорно-двигательного аппарата"),
            (5, "Дети с умственной отсталостью"),
            (6, "Дети с задержкой психического развития"),
            (7, "Дети с нарушением поведения и общения"),
            (
                8,
                "Дети с комплексными нарушениями психофизического развития, "
                "с так называемыми сложными дефектами "
                "(слепоглухонемые, глухие или слепые дети с умственной отсталостью)",
            ),
        ]

        with transaction.atomic():
            ViolationType.objects.filter(id__in=[v[0] for v in violations]).delete()

            for vid, vname in violations:
                ViolationType.objects.create(id=vid, name=vname)

        self.stdout.write(self.style.SUCCESS("Виды нарушений успешно созданы."))
