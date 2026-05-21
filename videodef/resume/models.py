from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
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
    DRAFT = "draft"
    ACTIVE = "active"

    STATUS_CHOICES = [
        (DRAFT, "Черновик"),
        (ACTIVE, "Активно"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    short_info = models.CharField(max_length=400, verbose_name="Краткая информация")
    detailed_info = models.TextField(max_length=5000, verbose_name="Подробная информация")
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Статус резюме"
    )
    documents = models.ManyToManyField(Document, blank=True, verbose_name="Документы")
    violation_types = models.ManyToManyField(
        ViolationType, blank=True, verbose_name="Виды нарушений"
    )

    # Новые поля для алгоритма Беллмана-Заде
    price_min = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Минимальная цена (₽)"
    )
    price_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Максимальная цена (₽)"
    )
    experience_years = models.PositiveIntegerField(
        default=0, verbose_name="Опыт работы (лет)"
    )
    education_level = models.PositiveIntegerField(
        default=0, verbose_name="Уровень образования (0-10)",
        help_text="0 - без образования, 10 - высшее профильное + учёная степень"
    )
    rating = models.FloatField(
        default=0, verbose_name="Рейтинг (0-5)"
    )
    location_lat = models.FloatField(null=True, blank=True, verbose_name="Широта")
    location_lon = models.FloatField(null=True, blank=True, verbose_name="Долгота")
    location_address = models.CharField(
        max_length=500, blank=True, verbose_name="Адрес"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"

    def __str__(self):
        return f"{self.short_info} ({'Активно' if self.status == self.ACTIVE else 'Черновик'})"

    def get_average_price(self):
        return (float(self.price_min) + float(self.price_max)) / 2


class ResumeImage(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="resume_images/")

    class Meta:
        verbose_name = "Изображение резюме"
        verbose_name_plural = "Изображения резюме"

    def __str__(self):
        if self.id:
            return f"Изображение №{self.id} для резюме №{self.resume.id}"
        return f"Несозданное изображение для резюме №{self.resume.id}"

class ExpertMatrixSettings(models.Model):
    """Настройки матрицы парных сравнений от эксперта"""
    matrix_data = models.JSONField(verbose_name="Данные матрицы")
    weights_data = models.JSONField(verbose_name="Веса критериев")
    consistency_ratio = models.FloatField(verbose_name="Отношение согласованности")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, 
        verbose_name="Обновлено экспертом"
    )
    
    class Meta:
        verbose_name = "Настройка матрицы эксперта"
        verbose_name_plural = "Настройки матриц эксперта"
    
    def __str__(self):
        return f"Матрица эксперта (ОС={self.consistency_ratio:.4f})"


class TeacherReview(models.Model):
    """Отзыв родителя о преподавателе"""
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews_received',
        verbose_name="Преподаватель"
    )
    parent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews_given',
        verbose_name="Родитель"
    )
    rating = models.IntegerField(
        verbose_name="Оценка",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка от 1 до 5"
    )
    comment = models.TextField(
        max_length=1000, verbose_name="Комментарий",
        help_text="Ваш отзыв о работе преподавателя"
    )
    is_approved = models.BooleanField(
        default=False, verbose_name="Проверен",
        help_text="Отзыв проверен администратором"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    
    class Meta:
        verbose_name = "Отзыв о преподавателе"
        verbose_name_plural = "Отзывы о преподавателях"
        unique_together = ['teacher', 'parent']  # Один отзыв от одного родителя
        
    def __str__(self):
        return f"Отзыв от {self.parent.profile} на {self.teacher.profile} - {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Обновляем рейтинг преподавателя
        self._update_teacher_rating()
    
    def _update_teacher_rating(self):
        """Обновление среднего рейтинга преподавателя"""
        reviews = TeacherReview.objects.filter(
            teacher=self.teacher, 
            is_approved=True
        )
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            # Обновляем рейтинг в резюме преподавателя
            Resume.objects.filter(user=self.teacher).update(rating=avg_rating)


class FuzzyComparisonSettings(models.Model):
    """
    Хранение настроек парных сравнений для метода Беллмана-Заде.
    Администратор может настраивать эти параметры через админ-панель.
    """
    criteria_comparisons = models.TextField(
        verbose_name="Сравнения критериев",
        blank=True,
        null=True,
        help_text="JSON с парными сравнениями критериев (шкала Саати)"
    )
    alternative_comparisons = models.TextField(
        verbose_name="Сравнения альтернатив",
        blank=True,
        null=True,
        help_text="JSON с парными сравнениями преподавателей по каждому критерию"
    )
    criteria_weights = models.TextField(
        verbose_name="Веса критериев",
        blank=True,
        null=True,
        help_text="JSON с рассчитанными весами критериев (α-коэффициенты)"
    )
    use_expert_comparisons = models.BooleanField(
        verbose_name="Использовать экспертные сравнения",
        default=False,
        help_text="Включить использование ручных экспертных парных сравнений"
    )
    updated_at = models.DateTimeField(auto_now=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Кто обновил"
    )
    
    class Meta:
        verbose_name = "Настройки нечеткого анализа (Беллман-Заде)"
        verbose_name_plural = "Настройки нечеткого анализа (Беллман-Заде)"
    
    def __str__(self):
        return f"Настройки Беллмана-Заде от {self.updated_at.strftime('%d.%m.%Y %H:%M')}"