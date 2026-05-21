from django.core.management.base import BaseCommand
from account.models import User
from resume.models import TeacherReview


class Command(BaseCommand):
    help = "Создание тестовых отзывов о преподавателях"

    def handle(self, *args, **kwargs):
        # Родители (user1 и user4)
        parent1 = User.objects.filter(username="user1").first()
        parent4 = User.objects.filter(username="user4").first()
        
        # Преподаватели (user2 и user3)
        teacher2 = User.objects.filter(username="user2").first()
        teacher3 = User.objects.filter(username="user3").first()

        if not all([parent1, parent4, teacher2, teacher3]):
            self.stdout.write(self.style.WARNING("Не все пользователи найдены"))
            return

        reviews_data = [
            {
                "teacher": teacher2,
                "parent": parent1,
                "rating": 5,
                "comment": "Замечательный логопед! Ребёнок стал говорить намного лучше уже через месяц занятий. Очень рекомендую!",
            },
            {
                "teacher": teacher2,
                "parent": parent4,
                "rating": 4,
                "comment": "Хороший специалист. Индивидуальный подход к ребёнку, интересные методики. Немного дороговато, но результат стоит того.",
            },
            {
                "teacher": teacher3,
                "parent": parent1,
                "rating": 5,
                "comment": "Алексей — прекрасный дефектолог. Помог нашему сыну с РАС адаптироваться и начать общаться. Огромная благодарность!",

            },
            {
                "teacher": teacher3,
                "parent": parent4,
                "rating": 4,
                "comment": "Грамотный подход, использует современные методики. Ребёнку нравится заниматься.",
            },
        ]

        for review_data in reviews_data:
            review, created = TeacherReview.objects.get_or_create(
                teacher=review_data["teacher"],
                parent=review_data["parent"],
                defaults={
                    "rating": review_data["rating"],
                    "comment": review_data["comment"],
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Создан отзыв: {review_data['parent'].username} → "
                        f"{review_data['teacher'].username} ({review_data['rating']}★)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Отзыв уже существует: {review_data['parent'].username} → "
                        f"{review_data['teacher'].username}"
                    )
                )