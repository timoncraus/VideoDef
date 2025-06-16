from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.timezone import now
from django.db import models
import random
import string
import os

CHARACTERS = string.ascii_uppercase + string.digits


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **kwargs):
        """Создание обычного пользователя"""
        if not username:
            raise ValueError("Пользователь должен иметь логин")
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **kwargs,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None):
        """Создание супер пользователя"""
        user = self.create_user(username=username, email=email, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def authenticate_user(self, identifier, password):
        """Аутентификация по ID, username, email или телефону"""
        user = None
        identifier = identifier.strip()
        if (
            all([letter in CHARACTERS for letter in identifier])
            and len(identifier) == 7
        ):
            user = self.model.objects.filter(unique_id=identifier).first()
        elif "@" in identifier:
            user = self.model.objects.filter(email=identifier).first()
        elif all([letter in "+0123456789" for letter in identifier]):
            user = self.model.objects.filter(phone_number=identifier).first()
        else:
            user = self.model.objects.filter(username=identifier).first()

        if not user:
            raise ValueError("Неверный логин")
        if not user.check_password(password):
            raise ValueError("Неверный пароль")
        return user


class Role(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название роли")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


class Gender(models.Model):
    name = models.CharField(max_length=20, verbose_name="Название пола")

    class Meta:
        verbose_name = "Пол"
        verbose_name_plural = "Пол"

    def __str__(self):
        return self.name


def get_random_filename():
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


def get_avatar_path(user, filename):
    _, ext = filename.split(".")
    path = os.path.join("avatars", get_random_filename() + "." + ext)
    while os.path.exists(path):
        path = os.path.join("avatars", get_random_filename() + "." + ext)
    return path


class Profile(models.Model):
    photo = models.ImageField(
        upload_to=get_avatar_path, blank=True, verbose_name="Фото"
    )
    first_name = models.CharField(max_length=40, verbose_name="Имя")
    last_name = models.CharField(max_length=40, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=40, blank=True, verbose_name="Отчество")
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, verbose_name="Роль"
    )
    gender = models.ForeignKey(
        Gender, on_delete=models.SET_NULL, null=True, verbose_name="Пол"
    )
    date_birth = models.DateField(verbose_name="Дата рождения")

    @property
    def role_display(self):
        if self.role:
            return self.role.name
        return "Неизвестно"

    def __str__(self):
        return f"{self.role_display} {self.last_name} {self.first_name} {self.patronymic or ''}".strip()

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    unique_id = models.CharField(
        max_length=7, unique=True, primary_key=True, verbose_name="ID"
    )
    username = models.CharField(max_length=64, unique=True, verbose_name="Логин")
    email = models.EmailField(max_length=255, unique=True, verbose_name="E-mail")
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name="Номер телефона"
    )
    date_registr = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Последний раз в сети")
    profile = models.OneToOneField(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="user",
        verbose_name="Профиль",
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    def update_last_seen(self):
        self.last_seen = now()
        self.save()

    def generate_unique_id(self):
        while True:
            new_id = "".join(random.choices(CHARACTERS, k=7))
            if not User.objects.filter(unique_id=new_id).exists():
                return new_id

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
