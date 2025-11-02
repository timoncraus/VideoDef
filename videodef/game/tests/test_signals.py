from unittest.mock import patch, MagicMock

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
            piece_positions=[1],
            preset_image_path=None,
            user_image=None,
        )

    @patch("game.signals.print")
    def test_delete_user_game_associated_files_simplified_deletes_file(
        self, mock_print
    ):
        mock_storage = MagicMock()
        mock_storage.exists.return_value = True

        mock_image = MagicMock()
        mock_image.name = "test.jpg"
        mock_image.storage = mock_storage
        mock_image.delete.return_value = None

        self.user_puzzle.user_image = mock_image

        user_game_pk = self.user_game.pk  # <- запоминаем PK ДО удаления

        with patch.object(mock_image, "delete") as mock_delete:
            self.user_game.delete()
            mock_delete.assert_called_once()
            mock_print.assert_any_call(
                f"SIGNAL: Файл 'test.jpg' для UserGame PK '{user_game_pk}' удален."
            )

    @patch("game.signals.print")
    def test_signal_handles_exception_gracefully(self, mock_print):
        mock_storage = MagicMock()
        mock_storage.exists.side_effect = Exception("Storage error")

        mock_image = MagicMock()
        mock_image.name = "test.jpg"
        mock_image.storage = mock_storage
        mock_image.delete.return_value = None

        self.user_puzzle.user_image = mock_image

        self.user_game.delete()

        self.assertTrue(
            any(
                "SIGNAL UNEXPECTED ERROR" in call.args[0]
                for call in mock_print.call_args_list
            )
        )
