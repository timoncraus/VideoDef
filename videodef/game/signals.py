from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import UserGame, UserPuzzle

@receiver(pre_delete, sender=UserGame)
def delete_user_game_associated_files_simplified(sender, instance, **kwargs):
    """
    Сигнал, вызываемый перед удалением объекта UserGame.
    Удаляет связанные файлы
    """
    try:
        if hasattr(instance, 'puzzle_details'):
            puzzle_details = instance.puzzle_details

            if puzzle_details:
                if puzzle_details.user_image and puzzle_details.user_image.name:
                    image_name = puzzle_details.user_image.name
                    storage = puzzle_details.user_image.storage

                    if storage.exists(image_name):
                        try:
                            puzzle_details.user_image.delete(save=False)
                            print(f"SIGNAL: Файл '{image_name}' для UserGame PK '{instance.pk}' удален.")
                        except Exception as e:
                            print(f"SIGNAL ERROR: Ошибка при удалении файла '{image_name}' для UserGame PK '{instance.pk}': {e}")
    except Exception as e:
        print(f"SIGNAL UNEXPECTED ERROR: Ошибка при обработке удаления файлов для UserGame PK '{instance.pk}': {e}")