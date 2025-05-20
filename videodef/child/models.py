from django.db import models

from account.models import User, Gender
from resume.models import ViolationType

class Child(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=400, verbose_name="Имя")
    info = models.TextField(max_length=5000, verbose_name="Информация")
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True, verbose_name="Пол")
    date_birth = models.DateField(verbose_name="Дата рождения")
    violation_types = models.ManyToManyField(ViolationType, blank=True, verbose_name="Виды нарушений")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ребенок"
        verbose_name_plural = "Дети"

    def __str__(self):
        return f"Ребенок №{self.id} ({self.name})"

class ChildImage(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='child_images/')

    class Meta:
        verbose_name = "Изображение ребенка"
        verbose_name_plural = "Изображения ребенка"

    def __str__(self):
        if self.id:
            return f"Изображение №{self.id} для ребенка №{self.child.id}"
        return f"Несозданное изображение для ребенка №{self.child.id}"