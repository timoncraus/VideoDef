from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
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
            piece_positions=[0, 1, 2, 3, 4, 5, 6, 7, 8],
            preset_image_path=None,
            user_image=None,
        )

    @patch("game.signals.print")
    def test_delete_user_game_associated_files_simplified_deletes_file(
        self, mock_print
    ):
        # Создаем реальный файл для теста
        test_file = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        # Присваиваем реальный файл
        self.user_puzzle.user_image = test_file
        self.user_puzzle.save()
        
        # Проверяем, что файл существует
        self.assertTrue(self.user_puzzle.user_image)
        
        # Запоминаем PK до удаления
        user_game_pk = self.user_game.pk
        
        # Сохраняем путь к файлу для проверки
        if hasattr(self.user_puzzle.user_image, 'path'):
            file_path = self.user_puzzle.user_image.path
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что файл был удален (если есть путь)
        if hasattr(self.user_puzzle.user_image, 'path'):
            self.assertFalse(os.path.exists(file_path))
        
        # Проверяем, что print был вызван
        mock_print.assert_any_call(
            f"SIGNAL: Файл пазла 'test.jpg' удален."
        )

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        # Создаем мок для изображения, но не присваиваем его напрямую
        # Вместо этого используем патч для метода delete
        test_file = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        self.user_puzzle.user_image = test_file
        self.user_puzzle.save()
        
        # Мокаем метод delete, чтобы вызвать исключение
        with patch.object(self.user_puzzle.user_image, 'delete', side_effect=Exception("Storage error")):
            # Удаляем игру - не должно быть исключений
            self.user_game.delete()
        
        # Проверяем, что была вызвана обработка ошибки
        mock_print.assert_any_call(
            f"SIGNAL UNEXPECTED ERROR: Ошибка при удалении файлов для UserGame PK '{self.user_game.pk}': Storage error"
        )