from django.db import models
from account.models import User
from document.models import Document

class ViolationType(models.Model):
    name = models.CharField(max_length=300)

    class Meta:
        verbose_name = "Вид нарушений"
        verbose_name_plural = "Виды нарушений"

    def __str__(self):
        return self.name


class Resume(models.Model):
    DRAFT = 'draft'
    ACTIVE = 'active'

    STATUS_CHOICES = [
        (DRAFT, 'Черновик'),
        (ACTIVE, 'Активно'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    short_info = models.CharField(max_length=400, verbose_name="Краткая информация")
    detailed_info = models.TextField(max_length=5000, verbose_name="Подробная информация")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Статус резюме")
    documents = models.ManyToManyField(Document, blank=True, verbose_name="Документы")
    violation_types = models.ManyToManyField(ViolationType, blank=True, verbose_name="Виды нарушений")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"

    def __str__(self):
        return f"{self.short_info} ({'Активно' if self.status == self.ACTIVE else 'Черновик'})"


class ResumeImage(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='resume_images/')

    class Meta:
        verbose_name = "Изображение резюме"
        verbose_name_plural = "Изображения резюме"

    def __str__(self):
        if self.id:
            return f"Изображение №{self.id} для резюме №{self.resume.id}"
        return f"Несозданное изображение для резюме №{self.resume.id}"
