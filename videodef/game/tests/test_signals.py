from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from game.models import UserGame, UserPuzzle
from game.tests.utils import GameTestBase


class SignalsTests(GameTestBase):
    """Тесты для сигналов модуля game."""
    
    def setUp(self):
        super().setUp()
        self.user_game = UserGame.objects.create(user=self.user, genre=self.genre)
        self.user_puzzle = UserPuzzle.objects.create(
            game=self.user_game,
            name="Puzzle1",
            grid_size=3,
            piece_positions=[0, 1, 2, 3, 4, 5, 6, 7, 8],
            preset_image_path=None,
            user_image=None,
        )

    @patch("game.signals.logger")
    def test_delete_user_game_associated_files_deletes_file(self, mock_logger):
        """Тест проверяет, что сигнал удаляет файл пазла при удалении игры."""
        # Создаем реальный файл
        test_file = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        # Присваиваем файл пазлу
        self.user_puzzle.user_image = test_file
        self.user_puzzle.save()
        
        # Проверяем, что файл сохранен
        self.assertTrue(self.user_puzzle.user_image)
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что logger.info был вызван
        mock_logger.info.assert_called()
        
        # Проверяем, что в сообщении есть слово "удален"
        calls = [str(call) for call in mock_logger.info.call_args_list]
        self.assertTrue(any("удален" in call for call in calls))

    @patch("game.signals.logger")
    def test_signal_handles_exception_gracefully(self, mock_logger):
        """Тест проверяет, что сигнал корректно обрабатывает исключения."""
        # Создаем реальный файл
        test_file = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        self.user_puzzle.user_image = test_file
        self.user_puzzle.save()
        
        # Мокаем delete, чтобы вызвать исключение
        with patch.object(self.user_puzzle.user_image, 'delete', side_effect=Exception("Storage error")):
            self.user_game.delete()
        
        # Проверяем, что ошибка была залогирована
        mock_logger.error.assert_called()
        
        # Проверяем, что в сообщении есть "SIGNAL UNEXPECTED ERROR"
        calls = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(any("SIGNAL UNEXPECTED ERROR" in call for call in calls))