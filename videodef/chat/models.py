from django.db import models
from account.models import User

# Create your models here.

class SmallChat(models.Model):
    name = models.CharField(max_length=255)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smallchat_user1_set')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smallchat_user2_set')

    def __str__(self):
        return self.name


class Message(models.Model):
    chat = models.ForeignKey(SmallChat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
