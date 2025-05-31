from django.db import models
from account.models import User


class SmallChat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='smallchat_user1_set', verbose_name="Пользователь 1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='smallchat_user2_set', verbose_name="Пользователь 2")

    def __str__(self):
        return f"Чат между пользователями {self.user1} и {self.user2}"

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class Message(models.Model):
    chat = models.ForeignKey(SmallChat, related_name='messages', on_delete=models.CASCADE, verbose_name="Чат")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Отправитель")
    content = models.TextField(max_length=1000, verbose_name="Содержимое")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправления")

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
