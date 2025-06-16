from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db import transaction
import os

from account.models import User
from document.models import Document, DocumentImage, DocumentVerificationStatus


class Command(BaseCommand):
    help = "Создание тестовых документов для резюме преподавателей"

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            default_status = DocumentVerificationStatus.objects.first()
            if not default_status:
                raise CommandError("Не найден ни один статус проверки документов.")
        except Exception as e:
            raise CommandError(f"Ошибка при получении статуса: {e}")

        documents_data = [
            {
                "username": "user2",
                "name": "Диплом логопеда",
                "info": "Диплом о высшем образовании по специальности 'Логопедия'.",
                "image_file": "photos/Мария_диплом.jpg",
            },
            {
                "username": "user3",
                "name": "Сертификат дефектолога",
                "info": "Сертификат повышения квалификации по работе с детьми с РАС.",
                "image_file": "photos/Алексей_сертификат.jpg",
            },
        ]

        for doc_data in documents_data:
            user = User.objects.filter(username=doc_data["username"]).first()
            if not user:
                self.stdout.write(
                    self.style.WARNING(f"Пользователь {doc_data['username']} не найден")
                )
                continue

            with transaction.atomic():
                document = Document.objects.create(
                    user=user,
                    name=doc_data["name"],
                    info=doc_data["info"],
                    ver_status=default_status,
                )

                image_path = os.path.join(base_dir, doc_data["image_file"])
                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        DocumentImage.objects.create(
                            document=document,
                            image=File(f, name=os.path.basename(image_path)),
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Документ с изображением создан для {doc_data['username']}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Изображение не найдено: {doc_data['image_file']}"
                        )
                    )
