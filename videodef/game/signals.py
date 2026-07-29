import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import UserGame

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=UserGame)
def delete_user_game_associated_files(sender, instance, **kwargs):
    """
    Сигнал, вызываемый перед удалением объекта UserGame.
    Удаляет связанные файлы для всех типов игр.
    
    Args:
        sender: Класс модели, отправившей сигнал (UserGame).
        instance: Экземпляр UserGame, который будет удален.
        **kwargs: Дополнительные аргументы сигнала.
    """
    try:
        # --- Обработка удаления файлов Пазлов ---
        if hasattr(instance, 'puzzle_details') and instance.puzzle_details:
            if instance.puzzle_details.user_image and instance.puzzle_details.user_image.name:
                instance.puzzle_details.user_image.delete(save=False)
                logger.info(f"SIGNAL: Файл пазла '{instance.puzzle_details.user_image.name}' удален.")
        
        # --- Обработка удаления файлов "Поиска пар" ---
        if hasattr(instance, 'memory_game_details') and instance.memory_game_details:
            instance.memory_game_details.delete_custom_images()

    except Exception as e:
        logger.error(f"SIGNAL UNEXPECTED ERROR: Ошибка при удалении файлов для UserGame PK '{instance.pk}': {e}", exc_info=True)