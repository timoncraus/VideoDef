from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
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
        # Создаем файл
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
        
        # Проверяем, что сигнал вызвал print
        mock_print.assert_any_call("SIGNAL: Файл пазла 'test_image.jpg' удален.")

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        # Создаем файл
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
        
        # Проверяем, что ошибка была обработана
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("SIGNAL UNEXPECTED ERROR" in call for call in calls))