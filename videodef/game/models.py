import os
import uuid

from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _


# ==========================================
# Утилиты и генераторы
# ==========================================

def generate_game_random_code(length: int = 10) -> str:
    """
    Генерирует случайную hex-строку для использования в уникальном ID игры.
    
    Args:
        length (int): Длина генерируемой строки. По умолчанию 10.
        
    Returns:
        str: Случайная строка в верхнем регистре.
    """
    return uuid.uuid4().hex[:length].upper()


def get_puzzle_image_path(instance: 'UserPuzzle', filename: str) -> str:
    """
    Генерирует уникальный путь для сохранения загружаемого изображения пазла.
    
    Args:
        instance (UserPuzzle): Экземпляр модели (не используется, но требуется сигнатурой Django).
        filename (str): Оригинальное имя загружаемого файла.
        
    Returns:
        str: Путь для сохранения файла в формате 'puzzle_images/<uuid>.<ext>'.
    """
    _, ext = os.path.splitext(filename)
    random_filename = uuid.uuid4().hex
    return os.path.join("puzzle_images", f"{random_filename}{ext}")


def get_memory_game_image_path(instance: 'UserMemoryGame', filename: str) -> str:
    """
    Генерирует уникальный путь для сохранения загружаемых изображений игры "Поиск пар".
    
    Args:
        instance (UserMemoryGame): Экземпляр модели.
        filename (str): Оригинальное имя загружаемого файла.
        
    Returns:
        str: Путь для сохранения файла в формате 'memory_game_images/<uuid>.<ext>'.
    """
    _, ext = os.path.splitext(filename)
    random_filename = uuid.uuid4().hex
    return os.path.join("memory_game_images", f"{random_filename}{ext}")


# ==========================================
# Модели игр
# ==========================================

class Genre(models.Model):
    """
    Модель жанра игры (например, 'Пазл', 'Поиск пар').
    Используется для категоризации пользовательских игр и генерации префикса ID.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Название жанра"),
        help_text=_("Полное название жанра игры (например, 'Пазл', 'Поиск пар')")
    )
    code = models.CharField(
        max_length=5,
        unique=True,
        verbose_name=_("Код жанра"),
        help_text=_("Короткий уникальный код для использования в ID игры (например, 'PZL')")
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Жанр игры")
        verbose_name_plural = _("Жанры игр")
        ordering = ['name']


class UserGame(models.Model):
    """
    Базовая модель пользовательской игры.
    Связывает пользователя и жанр, а также хранит уникальный идентификатор игры (game_id).
    """
    game_id = models.CharField(
        max_length=20,
        primary_key=True,
        editable=False,
        verbose_name=_("Уникальный ID игры"),
        help_text=_("Уникальный идентификатор игры формата ЖАНР-КОД (например, PZL-A1B2C3D4E5)")
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        related_name='user_games',
        verbose_name=_("Жанр игры")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_games',
        verbose_name=_("Пользователь"),
        db_index=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания игры"),
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата последнего обновления")
    )

    def save(self, *args, **kwargs) -> None:
        """
        Переопределенный метод сохранения.
        Автоматически генерирует уникальный game_id формата 'ЖАНР-КОД', если объект создается впервые.
        """
        if not self.pk:
            if not self.genre_id:
                raise ValueError("Невозможно сгенерировать game_id: не указан жанр игры.")
            
            try:
                genre_code = Genre.objects.get(pk=self.genre_id).code
            except Genre.DoesNotExist:
                raise ValueError(f"Жанр с ID {self.genre_id} не найден.")
            
            # Генерируем уникальный ID, проверяя наличие в БД
            while True:
                random_part = generate_game_random_code()
                new_id = f"{genre_code}-{random_part}"
                if not UserGame.objects.filter(pk=new_id).exists():
                    self.pk = new_id
                    break
        
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        username = self.user.username if self.user else _("Неизвестный пользователь")
        genre_name = self.genre.name if self.genre else _("Неизвестный жанр")
        return f"Игра {self.pk} ({genre_name}) от {username}"

    class Meta:
        verbose_name = _("Пользовательская игра")
        verbose_name_plural = _("Пользовательские игры")
        ordering = ['-created_at']


class UserPuzzle(models.Model):
    """
    Модель, хранящая специфичные данные для игры жанра 'Пазл'.
    Связана с UserGame через OneToOneField.
    """
    game = models.OneToOneField(
        UserGame,
        on_delete=models.CASCADE,
        related_name='puzzle_details',
        primary_key=True,
        verbose_name=_("Связь с базовой игрой")
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        verbose_name=_("Название пазла"),
        help_text=_("Название, которое пользователь дает созданному пазлу")
    )
    grid_size = models.PositiveSmallIntegerField(
        verbose_name=_("Размер сетки (N)"),
        help_text=_("Размер для сетки N x N")
    )
    piece_positions = models.JSONField(
        verbose_name=_("Позиции элементов пазла"),
        help_text=_("JSON-массив текущего расположения элементов пазла")
    )
    preset_image_path = models.CharField(
        max_length=100,
        blank=True, 
        null=True,
        verbose_name=_("Путь к пресету изображения"),
        help_text=_("Путь к изображению из стандартного набора (если используется)")
    )
    user_image = models.ImageField(
        upload_to=get_puzzle_image_path,
        blank=True, 
        null=True,
        verbose_name=_("Пользовательское изображение"),
        help_text=_("Изображение для пазла, загруженное пользователем")
    )

    @property
    def image_url(self) -> str | None:
        """
        Возвращает URL изображения пазла (пользовательского или пресета).
        
        Returns:
            str | None: URL изображения или None, если изображение не задано.
        """
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

    def clean(self) -> None:
        """
        Валидация модели перед сохранением.
        Проверяет наличие названия и корректность источника изображения.
        """
        super().clean()
        if not self.name:
            raise ValidationError({'name': _("Название не может быть пустым.")})
        
        if self.preset_image_path and self.user_image:
            raise ValidationError(_("Нельзя одновременно указать и пресет, и пользовательское изображение."))
        
        if not self.preset_image_path and not self.user_image:
            raise ValidationError(_("Необходимо указать либо путь к пресету, либо загрузить пользовательское изображение."))

    def __str__(self) -> str:
        return f"Данные пазла '{self.name}' ({self.grid_size}x{self.grid_size}) для игры {self.pk}"

    class Meta:
        verbose_name = _("Данные о пазле")
        verbose_name_plural = _("Данные о пазлах")


class UserMemoryGame(models.Model):
    """
    Модель, хранящая специфичные данные для игры жанра 'Поиск пар'.
    Связана с UserGame через OneToOneField.
    """
    game = models.OneToOneField(
        UserGame,
        on_delete=models.CASCADE,
        related_name='memory_game_details',
        primary_key=True,
        verbose_name=_("Связь с базовой игрой")
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        verbose_name=_("Название игры 'Поиск пар'"),
        help_text=_("Название, которое пользователь дает созданному экземпляру поиска пар")
    )
    pair_count = models.PositiveSmallIntegerField(
        verbose_name=_("Количество пар"),
        help_text=_("Количество пар изображений, которые нужно найти для победы в игре")
    )
    card_layout = models.JSONField(
        verbose_name=_("Расположение карточек"),
        help_text=_("JSON-массив индексов уникальных изображений (от 0 до pair_count-1)")
    )
    preset_name = models.CharField(
        max_length=50,
        blank=True, 
        null=True,
        verbose_name=_("Название пресета"),
        help_text=_("Название стандартного набора изображений (если используется)")
    )
    custom_image_paths = models.JSONField(
        blank=True, 
        null=True,
        verbose_name=_("Пути к пользовательским изображениям"),
        help_text=_("JSON-массив путей к файлам в медиа-хранилище")
    )

    def clean(self) -> None:
        """
        Валидация модели перед сохранением.
        Проверяет наличие названия, количество пар и корректность источника изображений.
        """
        super().clean()
        if not self.name:
            raise ValidationError({'name': _("Название не может быть пустым.")})
        if self.pair_count < 2:
            raise ValidationError({'pair_count': _("Количество пар должно быть не меньше 2.")})
        
        if self.preset_name and self.custom_image_paths:
            raise ValidationError(_("Нельзя одновременно указать и пресет, и пользовательские изображения."))
        if not self.preset_name and not self.custom_image_paths:
            raise ValidationError(_("Необходимо указать либо пресет, либо пользовательские изображения."))

    def delete_custom_images(self) -> None:
        """
        Удаляет все связанные пользовательские изображения с диска.
        Используется при удалении игры или обновлении набора изображений.
        """
        if self.custom_image_paths:
            for path in self.custom_image_paths:
                if default_storage.exists(path):
                    default_storage.delete(path)
            print(f"Удалены пользовательские изображения для игры {self.pk}")

    def __str__(self) -> str:
        return f"Данные игры '{self.name}' ({self.pair_count} пар) для {self.pk}"

    class Meta:
        verbose_name = _("Данные об игре 'Поиск пар'")
        verbose_name_plural = _("Данные об играх жанра 'Поиск пар'")