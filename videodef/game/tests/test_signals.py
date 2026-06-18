from unittest.mock import patch, MagicMock
from django.test import override_settings
from django.core.files.base import ContentFile
from game.models import UserGame, UserPuzzle
from game.tests.utils import GameTestBase
import os


class SignalsTests(GameTestBase):
    def setUp(self):
        super().setUp()
        self.user_game = UserGame.objects.create(user=self.user, genre=self.genre)
        self.user_puzzle = UserPuzzle.objects.create(
            game=self.user_game,
            name="Puzzle1",
            grid_size=3,
            piece_positions=[0, 1, 2, 3, 4, 5, 6, 7, 8],  # Правильные позиции для сетки 3x3
            preset_image_path=None,
            user_image=None,
        )

    @patch("game.signals.print")
    def test_delete_user_game_associated_files_simplified_deletes_file(
        self, mock_print
    ):
        # Создаем реальный файл для теста
        mock_image = MagicMock()
        mock_image.name = "test.jpg"
        mock_image.storage = MagicMock()
        mock_image.storage.exists.return_value = True
        mock_image.delete = MagicMock()
        
        # Присваиваем мок-изображение пазлу
        self.user_puzzle.user_image = mock_image
        self.user_puzzle.save()
        
        # Запоминаем PK до удаления
        user_game_pk = self.user_game.pk
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что delete был вызван
        mock_image.delete.assert_called_once_with(save=False)
        
        # Проверяем, что print был вызван с правильным сообщением
        mock_print.assert_any_call(
            f"SIGNAL: Файл пазла 'test.jpg' удален."
        )

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        # Создаем мок, который вызывает исключение при удалении
        mock_image = MagicMock()
        mock_image.name = "test.jpg"
        mock_image.storage = MagicMock()
        mock_image.storage.exists.return_value = True
        mock_image.delete.side_effect = Exception("Storage error")
        
        # Присваиваем мок-изображение пазлу
        self.user_puzzle.user_image = mock_image
        self.user_puzzle.save()
        
        # Удаляем игру - не должно быть исключений
        try:
            self.user_game.delete()
            exception_handled = True
        except Exception:
            exception_handled = False
        
        self.assertTrue(exception_handled)
        
        # Проверяем, что была вызвана обработка ошибки
        mock_print.assert_any_call(
            f"SIGNAL UNEXPECTED ERROR: Ошибка при удалении файлов для UserGame PK '{self.user_game.pk}': Storage error"
        )

    @patch("game.signals.print")
    def test_delete_user_game_with_no_image(self, mock_print):
        # Убеждаемся, что у пазла нет изображения
        self.user_puzzle.user_image = None
        self.user_puzzle.save()
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что print не вызывался для удаления файла
        # Но может быть вызван для других целей
        calls = [call.args[0] for call in mock_print.call_args_list]
        self.assertNotIn("SIGNAL: Файл пазла", str(calls))

    @patch("game.signals.print")
    def test_delete_user_game_with_memory_game(self, mock_print):
        # Создаем игру "Поиск пар"
        from game.models import UserMemoryGame, Genre
        
        memory_genre = Genre.objects.create(code='MEM', name='Поиск пар')
        memory_game = UserGame.objects.create(
            user=self.user,
            genre=memory_genre,
        )
        user_memory = UserMemoryGame.objects.create(
            game=memory_game,
            name="Memory Game",
            pair_count=2,
            card_layout=[0, 0, 1, 1],
            preset_name="fruits",
            custom_image_paths=None,
        )
        
        # Удаляем игру
        memory_game.delete()
        
        # Проверяем, что сигнал отработал без ошибок
        # (в сигнале вызывается delete_custom_images для memory_game_details)
        mock_print.assert_not_called()  # Или проверяем конкретные вызовы