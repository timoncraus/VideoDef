from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
import time

from account.models import User
from chat.models import SmallChat, Message


class Command(BaseCommand):
    help = "Создание тестовых сообщений для существующих чатов"

    def handle(self, *args, **kwargs):
        try:
            user1 = User.objects.get(username="user1")  # Ирина
            user2 = User.objects.get(username="user2")  # Мария
            user3 = User.objects.get(username="user3")  # Алексей
            user4 = User.objects.get(username="user4")  # Елена
        except ObjectDoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
            return

        message_data = [
            {
                "users": (user1, user2),
                "messages": [
                    (user1, "Здравствуйте, Мария! Нам посоветовали вас как логопеда."),
                    (user2, "Здравствуйте! Да, я занимаюсь с детьми 4-7 лет."),
                    (user1, "У дочки сложности с произношением 'р' и 'л'."),
                    (user2, "Понимаю, можем начать со следующей недели."),
                ],
            },
            {
                "users": (user1, user3),
                "messages": [
                    (user1, "Добрый день, Алексей! Слышали о вас хорошие отзывы."),
                    (user3, "Спасибо, приятно слышать. Чем могу помочь?"),
                    (user1, "Нужна помощь с развитием речи у сына 5 лет."),
                    (user3, "Конечно. Давайте созвонимся для обсуждения."),
                ],
            },
            {
                "users": (user4, user2),
                "messages": [
                    (user4, "Здравствуйте, Мария! Мы ищем дефектолога."),
                    (user2, "Здравствуйте! Я как раз специализируюсь на этом."),
                    (user4, "Ребёнок не разговаривает полными предложениями."),
                    (user2, "Давайте организуем первый видеозвонок."),
                ],
            },
            {
                "users": (user4, user3),
                "messages": [
                    (user4, "Алексей, добрый день! Вы работаете с детьми 3 лет?"),
                    (user3, "Здравствуйте! Да, с такими детьми я работаю."),
                    (user4, "Очень хорошо. Можем ли созвониться на следующей неделе?"),
                    (user3, "Конечно, я свободен во вторник и пятницу."),
                ],
            },
        ]

        for entry in message_data:
            u1, u2 = entry["users"]

            try:
                chat = SmallChat.objects.get(user1=u1, user2=u2)
            except SmallChat.DoesNotExist:
                try:
                    chat = SmallChat.objects.get(user1=u2, user2=u1)
                except SmallChat.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Чат между {u1.username} и {u2.username} не найден"
                        )
                    )
                    continue

            for sender, text in entry["messages"]:
                time.sleep(0.2)
                Message.objects.create(chat=chat, sender=sender, content=text)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Добавлены сообщения в чат {u1.username} <-> {u2.username}"
                )
            )
