from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db import transaction
import os

from account.models import User
from resume.models import Resume, ResumeImage, ViolationType
from document.models import Document


class Command(BaseCommand):
    help = "Создание тестовых резюме для преподавателей"

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            violation_types = list(ViolationType.objects.all())
        except ViolationType.DoesNotExist:
            raise CommandError("Не найдены типы нарушений.")

        teachers_by_username = {
            "user2": User.objects.filter(username="user2").first(),
            "user3": User.objects.filter(username="user3").first(),
        }

        documents_by_username = {
            "user2": Document.objects.filter(
                user=teachers_by_username["user2"]
            ).first(),
            "user3": Document.objects.filter(
                user=teachers_by_username["user3"]
            ).first(),
        }

        resume_data = [
            {
                "username": "user2",
                "short_info": "Логопед с 12-летним опытом работы",
                "detailed_info": (
                    "Работаю с детьми с речевыми нарушениями (ОНР, дизартрия, заикание). "
                    "Провожу индивидуальные и групповые занятия, сотрудничаю с психологами и дефектологами. "
                    "Помогаю детям успешно пройти подготовку к школе и адаптироваться в коллективе."
                ),
                "status": Resume.ACTIVE,
                "image_file": "photos/Мария_резюме.jpg",
            },
            {
                "username": "user3",
                "short_info": "Дефектолог по работе с детьми с РАС и ЗПР",
                "detailed_info": (
                    "Специализируюсь на обучении и сопровождении детей с расстройствами аутистического спектра \
                        и задержкой психического развития. "
                    "Провожу коррекционные занятия, использую методы ABA, TEACCH, альтернативную коммуникацию (PECS). "
                    "Опыт работы в инклюзивных и коррекционных учреждениях более 8 лет."
                ),
                "status": Resume.ACTIVE,
                "image_file": "photos/Алексей_резюме.jpg",
            },
        ]

        for resume_entry in resume_data:
            username = resume_entry["username"]
            user = teachers_by_username.get(username)

            if not user:
                self.stdout.write(
                    self.style.WARNING(f"Пользователь {username} не найден")
                )
                continue

            with transaction.atomic():
                resume = Resume.objects.create(
                    user=user,
                    short_info=resume_entry["short_info"],
                    detailed_info=resume_entry["detailed_info"],
                    status=resume_entry["status"],
                )

                document = documents_by_username.get(username)
                resume.documents.add(document)

                if violation_types:
                    resume.violation_types.set(violation_types[:3])

                image_path = os.path.join(base_dir, resume_entry["image_file"])
                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        ResumeImage.objects.create(
                            resume=resume,
                            image=File(f, name=os.path.basename(image_path)),
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Создано резюме для {username} с изображением"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Изображение не найдено: {resume_entry['image_file']}"
                        )
                    )
