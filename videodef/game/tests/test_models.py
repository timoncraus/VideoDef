from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from game.models import Genre, UserGame, UserPuzzle, UserMemoryGame, UserSoundLoto
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
        self.assertEqual(len(user_game.game_id), len(self.genre.code) + 1 + 10)

    def test_str_returns_correct_format(self):
        user_game = self.create_user_game()
        expected = f"Игра {user_game.game_id} ({self.genre.name}) от {self.user.username}"
        self.assertEqual(str(user_game), expected)

    def test_save_raises_without_genre(self):
        with self.assertRaises(ValueError):
            UserGame(user=self.user).save()


class UserPuzzleModelTests(GameTestBase):
    def test_clean_raises_if_no_name(self):
        puzzle = UserPuzzle(game=self.create_user_game(), name="", grid_size=2,
                            piece_positions=[0, 1, 2, 3], preset_image_path="p.png")
        with self.assertRaises(ValidationError) as cm:
            puzzle.clean()
        self.assertIn("name", cm.exception.message_dict)

    def test_clean_raises_if_both_preset_and_user_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        puzzle = UserPuzzle(game=self.create_user_game(), name="P", grid_size=2,
                            piece_positions=[0, 1, 2, 3], preset_image_path="p.png",
                            user_image=SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg"))
        with self.assertRaises(ValidationError):
            puzzle.clean()

    def test_clean_raises_if_neither_preset_nor_user_image(self):
        puzzle = UserPuzzle(game=self.create_user_game(), name="P", grid_size=2, piece_positions=[0, 1, 2, 3])
        with self.assertRaises(ValidationError):
            puzzle.clean()

    def test_str_returns_correct_string(self):
        puzzle = self.create_puzzle(grid_size=3, piece_positions=list(range(9)))
        self.assertIn("Puzzle1", str(puzzle))
        self.assertIn("3x3", str(puzzle))


class UserMemoryGameModelTests(GameTestBase):
    def test_clean_raises_if_no_name(self):
        game = UserMemoryGame(game=self.create_user_game(self.memory_genre), name="",
                              pair_count=2, card_layout=[0, 1, 0, 1], preset_name="fruits")
        with self.assertRaises(ValidationError) as cm:
            game.clean()
        self.assertIn("name", cm.exception.message_dict)

    def test_clean_raises_if_pair_count_too_small(self):
        game = UserMemoryGame(game=self.create_user_game(self.memory_genre), name="M",
                              pair_count=1, card_layout=[0, 0], preset_name="fruits")
        with self.assertRaises(ValidationError):
            game.clean()

    def test_clean_raises_if_both_preset_and_custom(self):
        game = UserMemoryGame(game=self.create_user_game(self.memory_genre), name="M",
                              pair_count=2, card_layout=[0, 1, 0, 1],
                              preset_name="fruits", custom_image_paths=["a.jpg"])
        with self.assertRaises(ValidationError):
            game.clean()

    def test_clean_raises_if_neither_preset_nor_custom(self):
        game = UserMemoryGame(game=self.create_user_game(self.memory_genre), name="M",
                              pair_count=2, card_layout=[0, 1, 0, 1])
        with self.assertRaises(ValidationError):
            game.clean()

    def test_str_returns_correct_string(self):
        game = self.create_memory_game()
        self.assertEqual(str(game), f"Данные игры 'Memory1' (2 пар) для {game.pk}")


class UserSoundLotoModelTests(GameTestBase):
    def test_clean_raises_if_no_name(self):
        game = UserSoundLoto(game=self.create_user_game(self.sound_loto_genre), name="",
                             rounds_count=3, cards_count=3, preset_name="animals")
        with self.assertRaises(ValidationError) as cm:
            game.clean()
        self.assertIn("name", cm.exception.message_dict)

    def test_clean_raises_if_rounds_out_of_range(self):
        game = UserSoundLoto(game=self.create_user_game(self.sound_loto_genre), name="S",
                             rounds_count=7, cards_count=3, preset_name="animals")
        with self.assertRaises(ValidationError):
            game.clean()

    def test_clean_raises_if_invalid_cards_count(self):
        game = UserSoundLoto(game=self.create_user_game(self.sound_loto_genre), name="S",
                             rounds_count=3, cards_count=5, preset_name="animals")
        with self.assertRaises(ValidationError):
            game.clean()

    def test_clean_raises_if_both_preset_and_custom(self):
        game = UserSoundLoto(game=self.create_user_game(self.sound_loto_genre), name="S",
                             rounds_count=3, cards_count=3, preset_name="animals",
                             custom_pairs=[{"image": "i.jpg", "audio": "a.mp3", "label": "L"}])
        with self.assertRaises(ValidationError):
            game.clean()

    def test_clean_raises_if_neither_preset_nor_custom(self):
        game = UserSoundLoto(game=self.create_user_game(self.sound_loto_genre), name="S",
                             rounds_count=3, cards_count=3)
        with self.assertRaises(ValidationError):
            game.clean()

    def test_str_contains_name(self):
        game = self.create_sound_loto()
        self.assertIn("SoundLoto1", str(game))

    def test_custom_pairs_stored_as_json(self):
        pairs = [{"image": "i.jpg", "audio": "a.mp3", "label": "Cat"}]
        game = self.create_sound_loto(preset_name=None, custom_pairs=pairs)
        game.refresh_from_db()
        self.assertEqual(game.custom_pairs, pairs)