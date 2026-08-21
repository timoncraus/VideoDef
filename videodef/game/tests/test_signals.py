from unittest.mock import patch

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from game.models import UserGame, UserSoundLoto
from game.tests.utils import GameTestBase


class PuzzleSignalsTests(GameTestBase):
    def setUp(self):
        super().setUp()
        self.puzzle = self.create_puzzle(preset_image_path=None, user_image=None)

    @patch("game.signals.logger")
    def test_deletes_puzzle_file(self, mock_logger):
        self.puzzle.user_image = SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg")
        self.puzzle.save()
        self.puzzle.game.delete()
        mock_logger.info.assert_called()

    @patch("game.signals.logger")
    def test_handles_exception_gracefully(self, mock_logger):
        self.puzzle.user_image = SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg")
        self.puzzle.save()
        with patch.object(self.puzzle.user_image, "delete", side_effect=Exception("boom")):
            self.puzzle.game.delete()
        mock_logger.error.assert_called()


class MemoryGameSignalsTests(GameTestBase):
    def test_deletes_custom_images(self):
        game = self.create_memory_game(custom_image_paths=None, preset_name=None)
        path = default_storage.save("memory_game_images/t.jpg", SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg"))
        game.custom_image_paths = [path]
        game.save()
        game.game.delete()
        self.assertFalse(default_storage.exists(path))


class SoundLotoSignalsTests(GameTestBase):
    def test_deletes_custom_files(self):
        game = self.create_sound_loto(preset_name=None, custom_pairs=None)
        img = default_storage.save("sound_loto_images/t.jpg", SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg"))
        aud = default_storage.save("sound_loto_audio/t.mp3", SimpleUploadedFile("t.mp3", b"x", content_type="audio/mpeg"))
        game.custom_pairs = [{"image": img, "audio": aud, "label": "L"}]
        game.save()
        game.game.delete()
        self.assertFalse(default_storage.exists(img))
        self.assertFalse(default_storage.exists(aud))
    
    def test_preset_game_deletes_nothing(self):
        game = self.create_sound_loto()
        game_pk = game.pk

        game.game.delete()

        self.assertFalse(UserGame.objects.filter(pk=game_pk).exists())
        self.assertFalse(UserSoundLoto.objects.filter(pk=game_pk).exists())