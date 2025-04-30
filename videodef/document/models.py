from django.db import models

class DocumentVerificationStatus(models.Model):
    name = models.TextField(verbose_name="Название статуса")

    class Meta:
        verbose_name = "Статус проверки"
        verbose_name_plural = "Статусы проверки"

    def __str__(self):
        return self.name
    

class Document(models.Model):
    photo = models.ImageField(upload_to='documents/')
    name = models.TextField(verbose_name="Название")
    info = models.TextField(verbose_name="Информация")
    ver_status = models.ForeignKey(DocumentVerificationStatus, on_delete=models.SET_NULL, null=True, verbose_name="Статус проверки")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self):
        return f"Документ №{self.id} ({'Проверен' if self.is_verified else 'На проверке'})"