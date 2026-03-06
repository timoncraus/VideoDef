from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.core.files.storage import default_storage 
import os
import random
import string
import uuid

class Genre(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название жанра",
        help_text="Полное название жанра игры (например, 'Пазл', 'Поиск пар')"
    )
    code = models.CharField(
        max_length=5,
        unique=True,
        verbose_name="Код жанра",
        help_text="Короткий уникальный код для использования в ID игры (например, 'PZL')"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Жанр игры"
        verbose_name_plural = "Жанры игр"
        ordering = ['name']

# --- Генерации случайной части ID игры ---
def generate_game_random_code(length=10):
    return uuid.uuid4().hex[:length].upper()

class UserGame(models.Model):
    game_id = models.CharField(
        max_length=20,
        primary_key=True,
        editable=False,
        verbose_name="Уникальный ID игры",
        help_text="Уникальный идентификатор игры формата ЖАНР-КОД"
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        related_name='user_games',
        verbose_name="Жанр игры"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_games',
        verbose_name="Пользователь",
        db_index=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания игры",
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего обновления"
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.genre_id:
                 raise ValueError("Невозможно сгенерировать game_id: не указан жанр игры.")
            try:
                genre = Genre.objects.get(pk=self.genre_id)
                genre_code = genre.code
            except Genre.DoesNotExist:
                raise ValueError(f"Жанр с ID {self.genre_id} не найден.")

            while True:
                random_part = generate_game_random_code()
                new_id = f"{genre_code}-{random_part}"

                if not UserGame.objects.filter(pk=new_id).exists():
                    self.pk = new_id
                    break
        
        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Неизвестный пользователь"
        genre_name = self.genre.name if self.genre else "Неизвестный жанр"
        return f"Игра {self.pk} ({genre_name}) от {username}"

    class Meta:
        verbose_name = "Пользовательская игра"
        verbose_name_plural = "Пользовательские игры"
        ordering = ['-created_at']

# --- Функция для генерации пути сохранения загружаемых изображений пазлов ---
def get_puzzle_image_path(instance, filename):
    _, ext = os.path.splitext(filename)
    random_filename = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32))
    path = os.path.join("puzzle_images", f"{random_filename}{ext}")
    return path

class UserPuzzle(models.Model):
    game = models.OneToOneField(
        UserGame,
        on_delete=models.CASCADE,
        related_name='puzzle_details',
        primary_key=True
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        verbose_name="Название пазла",
        help_text="Название, которое пользователь дает созданному пазлу"
    )
    grid_size = models.PositiveSmallIntegerField(
        verbose_name="Размер сетки (N)",
        help_text="Размер для сетки N x N"
    )
    piece_positions = models.JSONField(
        verbose_name="Позиции элементов пазла",
        help_text="JSON-массив текущего расположения элементов пазла"
    )
    preset_image_path = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name="Путь к пресету изображения",
        help_text="Путь к изображению из стандартного набора (если используется)"
    )
    user_image = models.ImageField(
        upload_to=get_puzzle_image_path,
        blank=True, null=True,
        verbose_name="Пользовательское изображение",
        help_text="Изображение для пазла, загруженное пользователем"
    )

    @property
    def image_url(self):
        if self.user_image:
            try:
                return self.user_image.url
            except ValueError:
                return None
        elif self.preset_image_path:
            try:
                return static(self.preset_image_path)
            except Exception:
                 return self.preset_image_path
        return None

    def clean(self):
        super().clean()

        if not self.name:
             raise ValidationError({'name': "Название не может быть пустым."})

        if self.preset_image_path and self.user_image:
            raise ValidationError("Нельзя одновременно указать и пресет, и пользовательское изображение.")
        if not self.preset_image_path and not self.user_image:
            raise ValidationError("Необходимо указать либо путь к пресету, либо загрузить пользовательское изображение.")

    def __str__(self):
        return f"Данные пазла '{self.name}' ({self.grid_size}x{self.grid_size}) для игры {self.pk}"

    class Meta:
        verbose_name = "Данные о пазле"
        verbose_name_plural = "Данные о пазлах"

# --- Функция для генерации пути сохранения загружаемых изображений для поиска пар ---
def get_memory_game_image_path(instance, filename):
    _, ext = os.path.splitext(filename)
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("memory_game_images", random_filename)


class UserMemoryGame(models.Model):
    game = models.OneToOneField(
        UserGame,
        on_delete=models.CASCADE,
        related_name='memory_game_details',
        primary_key=True
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        verbose_name="Название игры 'Поиск пар'",
        help_text="Название, которое пользователь дает созданному экземпляру поиска пар"
    )
    pair_count = models.PositiveSmallIntegerField(
        verbose_name="Количество пар",
        help_text="Количество пар изображений, которые нужно найти для победы в игре"
    )
    card_layout = models.JSONField(
        verbose_name="Расположение карточек",
        help_text="JSON-массив индексов уникальных изображений (от 0 до pair_count-1)"
    )
    preset_name = models.CharField(
        max_length=50,
        blank=True, null=True,
        verbose_name="Название пресета",
        help_text="Название стандартного набора изображений (если используется)"
    )
    custom_image_paths = models.JSONField(
        blank=True, null=True,
        verbose_name="Пути к пользовательским изображениям",
        help_text="JSON-массив путей к файлам в медиа-хранилище"
    )

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError({'name': "Название не может быть пустым."})
        if self.pair_count < 2:
            raise ValidationError({'pair_count': "Количество пар должно быть не меньше 2."})
        
        if self.preset_name and self.custom_image_paths:
            raise ValidationError("Нельзя одновременно указать и пресет, и пользовательские изображения.")
        if not self.preset_name and not self.custom_image_paths:
            raise ValidationError("Необходимо указать либо пресет, либо пользовательские изображения.")

    def __str__(self):
        return f"Данные игры '{self.name}' ({self.pair_count} пар) для {self.pk}"

    def delete_custom_images(self):
        """Метод для удаления связанных файлов с диска."""
        if self.custom_image_paths:
            for path in self.custom_image_paths:
                if default_storage.exists(path):
                    default_storage.delete(path)
            print(f"Удалены пользовательские изображения для игры {self.pk}")

    class Meta:
        verbose_name = "Данные об игре 'Поиск пар'"
        verbose_name_plural = "Данные об играх жанра 'Поиск пар'"