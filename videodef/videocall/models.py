from django.db import models
from account.models import User

class VideoCall(models.Model):
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    room_name = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    accepted = models.BooleanField(default=False)

    def duration(self):
        if self.ended_at:
            delta = self.ended_at - self.started_at
            minutes, seconds = divmod(delta.total_seconds(), 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                return f"{int(hours)}ч {int(minutes)}м"
            return f"{int(minutes)}м {int(seconds)}с"
        return None

    def __str__(self):
        return f"{self.caller} → {self.receiver} [{self.room_name}]"

    class Meta:
        verbose_name = "Видеозвонок"
        verbose_name_plural = "Видеозвонки"