from django.core.management.base import BaseCommand
from django.db import transaction

from document.models import DocumentVerificationStatus


class Command(BaseCommand):
    help = "Создание статусов проверки документов"

    def handle(self, *args, **kwargs):
        statuses = [
            (1, "На проверке"),
            (2, "Проверено"),
            (3, "Отказано"),
        ]

        with transaction.atomic():
            DocumentVerificationStatus.objects.filter(
                id__in=[s[0] for s in statuses]
            ).delete()

            for sid, sname in statuses:
                DocumentVerificationStatus.objects.create(id=sid, name=sname)

        self.stdout.write(
            self.style.SUCCESS("Статусы проверки документов успешно созданы.")
        )
