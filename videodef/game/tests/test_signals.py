from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
import tempfile
import os

from game.models import UserGame, UserPuzzle
from game.tests.utils import GameTestBase


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
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b'file_content')
            tmp_file_path = tmp_file.name
        
        try:
            # Создаем SimpleUploadedFile
            test_file = SimpleUploadedFile(
                os.path.basename(tmp_file_path),
                b'file_content',
                content_type='image/jpeg'
            )
            
            # Присваиваем файл пазлу
            self.user_puzzle.user_image = test_file
            self.user_puzzle.save()
            
            # Удаляем игру
            self.user_game.delete()
            
            # Проверяем, что print был вызван
            mock_print.assert_any_call(
                f"SIGNAL: Файл пазла '{os.path.basename(tmp_file_path)}' удален."
            )
        finally:
            # Удаляем временный файл если он существует
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        # Создаем мок для изображения
        mock_image = MagicMock()
        mock_image.name = "test.jpg"
        mock_image.delete.side_effect = Exception("Storage error")
        
        # Присваиваем мок пазлу
        self.user_puzzle.user_image = mock_image
        self.user_puzzle.save()
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что ошибка была обработана
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("SIGNAL UNEXPECTED ERROR" in call for call in calls))