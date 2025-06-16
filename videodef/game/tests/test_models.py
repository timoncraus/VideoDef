from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from game.models import Genre, UserGame, UserPuzzle
from game.tests.utils import GameTestBase

User = get_user_model()


class GenreModelTests(TestCase):
    def test_str_returns_name(self):
        genre = Genre.objects.create(name="Пазл", code="PZL")
        self.assertEqual(str(genre), "Пазл")


class UserGameModelTests(GameTestBase):
    def test_game_id_is_generated_on_save(self):
        user_game = UserGame(user=self.user, genre=self.genre)
        user_game.save()
        self.assertTrue(user_game.game_id.startswith(self.genre.code + "-"))
        self.assertEqual(
            len(user_game.game_id), len(self.genre.code) + 1 + 10
        )  # код + '-' + 10 символов

    def test_str_returns_correct_format(self):
        user_game = UserGame(user=self.user, genre=self.genre)
        user_game.save()
        expected_str = (
            f"Игра {user_game.game_id} ({self.genre.name}) от {self.user.username}"
        )
        self.assertEqual(str(user_game), expected_str)

    def test_save_raises_without_genre(self):
        user_game = UserGame(user=self.user)
        with self.assertRaises(ValueError):
            user_game.save()


class UserPuzzleModelTests(GameTestBase):
    def setUp(self):
        super().setUp()
        self.user_game = UserGame(user=self.user, genre=self.genre)
        self.user_game.save()

    def test_clean_raises_if_no_name(self):
        puzzle = UserPuzzle(
            game=self.user_game,
            name="",
            grid_size=3,
            piece_positions=[1],
            preset_image_path="preset.png",
        )
        with self.assertRaises(ValidationError) as cm:
            puzzle.clean()
        self.assertIn("name", cm.exception.message_dict)

    def test_clean_raises_if_both_preset_and_user_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        user_image = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        puzzle = UserPuzzle(
            game=self.user_game,
            name="Puzzle1",
            grid_size=3,
            piece_positions=[1],
            preset_image_path="preset.png",
            user_image=user_image,
        )
        with self.assertRaises(ValidationError):
            puzzle.clean()

    def test_clean_raises_if_neither_preset_nor_user_image(self):
        puzzle = UserPuzzle(
            game=self.user_game, name="Puzzle1", grid_size=3, piece_positions=[1]
        )
        with self.assertRaises(ValidationError):
            puzzle.clean()

    def test_str_returns_correct_string(self):
        puzzle = UserPuzzle(
            game=self.user_game,
            name="Puzzle1",
            grid_size=3,
            piece_positions=[1],
            preset_image_path="preset.png",
        )
        puzzle.save()
        expected_str = f"Данные пазла 'Puzzle1' (3x3) для игры {self.user_game.game_id}"
        self.assertEqual(str(puzzle), expected_str)
