from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from datetime import date
import os
from django.core.exceptions import ObjectDoesNotExist

from account.models import User, Gender
from resume.models import ViolationType
from child.models import Child, ChildImage


class Command(BaseCommand):
    help = "Создание тестовых детей"

    def handle(self, *args, **kwargs):
        try:
            gender_male = Gender.objects.get(name="Мужской")
            gender_female = Gender.objects.get(name="Женский")
        except ObjectDoesNotExist as e:
            raise CommandError(f"Не найдены обязательные значения пола: {e}")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        violation_types = list(ViolationType.objects.all())

        # Словарь пользователей-родителей
        parents_by_username = {
            "user1": User.objects.filter(username="user1").first(),
            "user4": User.objects.filter(username="user4").first(),
        }

        children_data = [
            {
                "parent_username": "user1",
                "name": "Олеся Сахарова",
                "info": "Очень активный ребёнок",
                "gender": gender_female,
                "date_birth": date(2015, 6, 15),
                "image_file": "photos/Олеся.jpg",
            },
            {
                "parent_username": "user1",
                "name": "Анна Иванова",
                "info": "Любит рисовать и читать",
                "gender": gender_female,
                "date_birth": date(2017, 8, 22),
                "image_file": "photos/Анна.jpg",
            },
            {
                "parent_username": "user4",
                "name": "Марк Кузнецов",
                "info": "Интересуется наукой и роботами",
                "gender": gender_male,
                "date_birth": date(2016, 3, 10),
                "image_file": "photos/Марк.jpg",
            },
        ]

        for child_data in children_data:
            parent = parents_by_username.get(child_data["parent_username"])
            if not parent:
                self.stdout.write(
                    self.style.WARNING(
                        f"Родитель {child_data['parent_username']} не найден"
                    )
                )
                continue

            child = Child.objects.create(
                user=parent,
                name=child_data["name"],
                info=child_data["info"],
                gender=child_data["gender"],
                date_birth=child_data["date_birth"],
            )

            if violation_types:
                child.violation_types.set(violation_types[:2])

            image_path = os.path.join(base_dir, child_data["image_file"])
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    ChildImage.objects.create(
                        child=child,
                        image=File(f, name=os.path.basename(image_path)),
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"Создан ребенок {child.name} с изображением")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Файл изображения не найден: {child_data['image_file']}"
                    )
                )
