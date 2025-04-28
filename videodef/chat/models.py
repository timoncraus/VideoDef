from django.db import models
from account.models import User


class SmallChat(models.Model):
    name = models.CharField(max_length=255)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smallchat_user1_set')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smallchat_user2_set')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class Message(models.Model):
    chat = models.ForeignKey(SmallChat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
