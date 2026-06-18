from unittest.mock import patch
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
        # Создаем мок для файла
        mock_image = MagicMock()
        mock_image.name = "test_image.jpg"
        
        # Присваиваем мок пазлу
        self.user_puzzle.user_image = mock_image
        self.user_puzzle.save()
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что delete был вызван
        mock_image.delete.assert_called_once_with(save=False)
        
        # Проверяем, что print был вызван
        mock_print.assert_any_call("SIGNAL: Файл пазла 'test_image.jpg' удален.")

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        # Создаем мок с исключением
        mock_image = MagicMock()
        mock_image.name = "test_image.jpg"
        mock_image.delete.side_effect = Exception("Storage error")
        
        self.user_puzzle.user_image = mock_image
        self.user_puzzle.save()
        
        # Удаляем игру
        self.user_game.delete()
        
        # Проверяем, что ошибка была обработана
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("SIGNAL UNEXPECTED ERROR" in call for call in calls))