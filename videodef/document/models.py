from django.db import models
from account.models import User

class DocumentVerificationStatus(models.Model):
    name = models.TextField(verbose_name="Название статуса")

    class Meta:
        verbose_name = "Статус проверки"
        verbose_name_plural = "Статусы проверки"

    def __str__(self):
        return self.name

def get_default_ver_status():
    try:
        return DocumentVerificationStatus.objects.get(pk=1).pk
    except DocumentVerificationStatus.DoesNotExist:
        return None

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=400, verbose_name="Название")
    info = models.TextField(max_length=5000, verbose_name="Информация")
    ver_status = models.ForeignKey(DocumentVerificationStatus, on_delete=models.SET_NULL, default=get_default_ver_status, null=True, verbose_name="Статус проверки")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self):
        return f"Документ №{self.id} ({self.ver_status})"


class DocumentImage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='document_images/')

    class Meta:
        verbose_name = "Изображение документа"
        verbose_name_plural = "Изображения документа"

    def __str__(self):
        return f"Изображение для документа №{self.document.id}"