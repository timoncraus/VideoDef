import json
import shutil
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import InternalError
from django.test import TestCase

from game.utils import (
    parse_and_validate_puzzle_data,
    parse_and_validate_memory_game_data,
    parse_and_validate_sound_loto_data,
    handle_db_integrity_error,
    cleanup_uploaded_files,
    save_memory_game_custom_images,
    save_sound_loto_custom_files,
    cleanup_sound_loto_custom_files,
)


class ParseAndValidatePuzzleDataTests(TestCase):
    def test_valid_data_with_preset(self):
        result = parse_and_validate_puzzle_data({
            "name": "Test Puzzle", "gridSize": "3",
            "piecePositions": json.dumps(list(range(9))), "preset_image_path": "preset.png",
        })
        self.assertEqual(result["name"], "Test Puzzle")
        self.assertEqual(result["grid_size"], 3)
        self.assertEqual(result["preset_path"], "preset.png")
        self.assertIsNone(result["uploaded_image_file"])

    def test_valid_data_with_uploaded_image(self):
        f = SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg")
        result = parse_and_validate_puzzle_data(
            {"name": "P", "gridSize": "2", "piecePositions": json.dumps([0, 1, 2, 3])},
            {"user_image_file": f},
        )
        self.assertIsNotNone(result["uploaded_image_file"])

    def test_empty_name_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_puzzle_data({"name": "", "gridSize": "2", "piecePositions": json.dumps([0, 1, 2, 3])})

    def test_invalid_grid_size_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_puzzle_data({"name": "T", "gridSize": "1", "piecePositions": json.dumps([0])})

    def test_positions_length_mismatch_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_puzzle_data({"name": "T", "gridSize": "3", "piecePositions": json.dumps([0, 1])})

    def test_invalid_json_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_puzzle_data({"name": "T", "gridSize": "2", "piecePositions": "bad"})


class ParseAndValidateMemoryGameDataTests(TestCase):
    def test_valid_data_with_preset(self):
        result = parse_and_validate_memory_game_data({
            "name": "M", "pairCount": "2", "cardLayout": json.dumps([0, 1, 0, 1]), "presetName": "fruits",
        })
        self.assertEqual(result["pair_count"], 2)
        self.assertEqual(result["preset_name"], "fruits")

    def test_valid_data_with_custom_images(self):
        files = {"customImages[]": [
            SimpleUploadedFile("a.jpg", b"1", content_type="image/jpeg"),
            SimpleUploadedFile("b.jpg", b"2", content_type="image/jpeg"),
        ]}
        result = parse_and_validate_memory_game_data(
            {"name": "M", "pairCount": "2", "cardLayout": json.dumps([0, 1, 0, 1])}, files,
        )
        self.assertEqual(len(result["custom_images"]), 2)

    def test_empty_name_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_memory_game_data({"name": "", "pairCount": "2", "cardLayout": json.dumps([0, 1, 0, 1])})

    def test_invalid_pair_count_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_memory_game_data({"name": "M", "pairCount": "1", "cardLayout": json.dumps([0, 0])})

    def test_card_layout_mismatch_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_memory_game_data({"name": "M", "pairCount": "2", "cardLayout": json.dumps([0, 1])})


class ParseAndValidateSoundLotoDataTests(TestCase):
    def _files(self, n=2):
        return {
            "customImages[]": [SimpleUploadedFile(f"i{k}.jpg", b"x", content_type="image/jpeg") for k in range(n)],
            "customAudios[]": [SimpleUploadedFile(f"a{k}.mp3", b"x", content_type="audio/mpeg") for k in range(n)],
        }

    def test_valid_data_with_preset(self):
        result = parse_and_validate_sound_loto_data({
            "name": "S", "roundsCount": "3", "cardsCount": "3", "presetName": "animals",
        })
        self.assertEqual(result["rounds_count"], 3)
        self.assertEqual(result["preset_name"], "animals")
        self.assertTrue(result["autoplay"])

    def test_valid_data_with_custom_files(self):
        result = parse_and_validate_sound_loto_data(
            {"name": "S", "roundsCount": "2", "cardsCount": "2", "customLabels": json.dumps(["A", "B"])},
            self._files(2),
        )
        self.assertEqual(len(result["custom_images"]), 2)
        self.assertEqual(result["custom_labels"], ["A", "B"])

    def test_empty_name_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data({"name": "", "roundsCount": "2", "cardsCount": "2", "presetName": "animals"})

    def test_rounds_out_of_range_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data({"name": "S", "roundsCount": "7", "cardsCount": "2", "presetName": "animals"})

    def test_invalid_cards_count_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data({"name": "S", "roundsCount": "2", "cardsCount": "5", "presetName": "animals"})

    def test_image_audio_count_mismatch_raises_error(self):
        files = self._files(2)
        files["customAudios[]"] = files["customAudios[]"][:1]
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data(
                {"name": "S", "roundsCount": "2", "cardsCount": "2", "customLabels": json.dumps(["A", "B"])}, files,
            )

    def test_insufficient_pairs_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data(
                {"name": "S", "roundsCount": "4", "cardsCount": "2", "customLabels": json.dumps(["A", "B"])},
                self._files(2),
            )

    def test_preset_and_custom_simultaneously_raises_error(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data(
                {"name": "S", "roundsCount": "2", "cardsCount": "2", "presetName": "animals", "customLabels": json.dumps(["A", "B"])},
                self._files(2),
            )

    def test_create_mode_requires_source(self):
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data({"name": "S", "roundsCount": "2", "cardsCount": "2"})

    def test_update_mode_allows_no_source(self):
        result = parse_and_validate_sound_loto_data(
            {"name": "S", "roundsCount": "2", "cardsCount": "2", "customLabels": json.dumps(["A", "B"]),
             "audioOrder": json.dumps([1, 0])},
            is_update=True,
        )
        self.assertEqual(result["audio_order"], [1, 0])

    def test_bad_audio_extension_raises_error(self):
        files = self._files(2)
        files["customAudios[]"][0] = SimpleUploadedFile("a.txt", b"x", content_type="text/plain")
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data(
                {"name": "S", "roundsCount": "2", "cardsCount": "2", "customLabels": json.dumps(["A", "B"])}, files,
            )

    @patch("game.utils.MAX_AUDIO_FILE_SIZE", 10)
    def test_audio_too_large_raises_error(self):
        files = self._files(2)
        files["customAudios[]"][0] = SimpleUploadedFile("a.mp3", b"x" * 20, content_type="audio/mpeg")
        with self.assertRaises(ValueError):
            parse_and_validate_sound_loto_data(
                {"name": "S", "roundsCount": "2", "cardsCount": "2", "customLabels": json.dumps(["A", "B"])}, files,
            )


class HandleDbIntegrityErrorTests(TestCase):
    def test_puzzle_duplicate_error(self):
        resp = handle_db_integrity_error(InternalError('пазл с названием "T" уже существует'), "puzzle", "T")
        self.assertEqual(resp.status_code, 400)

    def test_memory_game_duplicate_error(self):
        resp = handle_db_integrity_error(InternalError('игра "поиск пар" с названием "T" уже существует'), "memory_game", "T")
        self.assertEqual(resp.status_code, 400)

    def test_sound_loto_duplicate_error(self):
        resp = handle_db_integrity_error(InternalError('игра "звуковое лото" с названием "T" уже существует'), "sound_loto", "T")
        self.assertEqual(resp.status_code, 400)

    def test_unexpected_db_error(self):
        resp = handle_db_integrity_error(InternalError("boom"), "puzzle", "T")
        self.assertEqual(resp.status_code, 500)


class CleanupUploadedFilesTests(TestCase):
    def tearDown(self):
        shutil.rmtree(Path(settings.MEDIA_ROOT) / "test_cleanup", ignore_errors=True)
        super().tearDown()

    def test_cleanup_existing_files(self):
        path = default_storage.save("test_cleanup/t.jpg", SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg"))
        self.assertTrue(default_storage.exists(path))
        cleanup_uploaded_files([path])
        self.assertFalse(default_storage.exists(path))

    def test_cleanup_nonexistent_files(self):
        cleanup_uploaded_files(["nope/f.jpg"])


class SaveMemoryGameCustomImagesTests(TestCase):
    def tearDown(self):
        shutil.rmtree(Path(settings.MEDIA_ROOT) / "memory_game_images", ignore_errors=True)
        super().tearDown()

    def test_save_success(self):
        paths = save_memory_game_custom_images(
            [SimpleUploadedFile("a.jpg", b"1", content_type="image/jpeg"),
             SimpleUploadedFile("b.jpg", b"2", content_type="image/jpeg")], 2,
        )
        self.assertEqual(len(paths), 2)
        cleanup_uploaded_files(paths)

    def test_insufficient_raises_error(self):
        with self.assertRaises(ValueError):
            save_memory_game_custom_images([SimpleUploadedFile("a.jpg", b"1", content_type="image/jpeg")], 2)


class SaveSoundLotoCustomFilesTests(TestCase):
    def tearDown(self):
        shutil.rmtree(Path(settings.MEDIA_ROOT) / "sound_loto_images", ignore_errors=True)
        shutil.rmtree(Path(settings.MEDIA_ROOT) / "sound_loto_audio", ignore_errors=True)
        super().tearDown()

    def test_save_success(self):
        pairs = save_sound_loto_custom_files(
            [SimpleUploadedFile("i.jpg", b"1", content_type="image/jpeg")],
            [SimpleUploadedFile("a.mp3", b"2", content_type="audio/mpeg")],
            ["Cat"],
        )
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["label"], "Cat")
        self.assertTrue(default_storage.exists(pairs[0]["image"]))
        cleanup_sound_loto_custom_files(pairs)

    def test_mismatch_raises_error(self):
        with self.assertRaises(ValueError):
            save_sound_loto_custom_files(
                [SimpleUploadedFile("i.jpg", b"1", content_type="image/jpeg")],
                [], ["Cat"],
            )


class CleanupSoundLotoCustomFilesTests(TestCase):
    def test_cleanup_existing_pairs(self):
        img = default_storage.save("sound_loto_images/t.jpg", SimpleUploadedFile("t.jpg", b"x", content_type="image/jpeg"))
        aud = default_storage.save("sound_loto_audio/t.mp3", SimpleUploadedFile("t.mp3", b"x", content_type="audio/mpeg"))
        cleanup_sound_loto_custom_files([{"image": img, "audio": aud, "label": "L"}])
        self.assertFalse(default_storage.exists(img))
        self.assertFalse(default_storage.exists(aud))

    def test_cleanup_handles_missing_keys(self):
        cleanup_sound_loto_custom_files([{"label": "no files"}])