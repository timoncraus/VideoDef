from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random
import string


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **kwargs):
        if not username:
            raise ValueError("Пользователь должен иметь логин")
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **kwargs,
        )
        user.set_password(password)  # Хешируем пароль
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None):
        user = self.create_user(username=username, email=email, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class ViolationType(models.Model):
    name = models.CharField(max_length=150)

    class Meta:
        verbose_name = "Виды нарушений"

    def __str__(self):
        return self.name


CHARACTERS = string.ascii_uppercase + string.digits


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    ROLE_TEACHER = "T"
    ROLE_STUDENT = "S"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Учитель"),
        (ROLE_STUDENT, "Ученик"),
    ]

    unique_id = models.CharField(max_length=7, unique=True, primary_key=True, verbose_name="ID")
    username = models.CharField(max_length=64, unique=True, verbose_name="Логин")
    first_name = models.CharField(max_length=40, verbose_name="Имя")
    last_name = models.CharField(max_length=40, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=40, blank=True, verbose_name="Отчество")
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, verbose_name="Роль")
    photo = models.ImageField(upload_to="images", blank=True, verbose_name="Фото")
    email = models.EmailField(max_length=255, unique=True, verbose_name="E-mail")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    date_registr = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    date_last_edit = models.DateTimeField(auto_now=True, verbose_name="Дата последнего редактирования")
    date_birth = models.DateField(verbose_name="Дата рождения")
    violations = models.ManyToManyField(ViolationType)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    def generate_unique_id(self):
        while True:
            new_id = "".join(random.choices(CHARACTERS, k=7))
            if not User.objects.filter(unique_id=new_id).exists():
                return new_id

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    @property
    def role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, "Неизвестно")

    def __str__(self):
        return f"{self.role_display} {self.last_name} {self.first_name} {self.patronymic or ''}".strip()