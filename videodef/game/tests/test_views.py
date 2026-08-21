import json

from django.test import Client
from django.test.client import BOUNDARY, encode_multipart
from django.urls import reverse

from game.models import UserGame, UserPuzzle, UserMemoryGame, UserSoundLoto
from game.tests.utils import GameTestBase


class GameViewsTest(GameTestBase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.login(username="user1", password="pass1234")
        self.user_game = self.create_user_game()
        self.user_puzzle = UserPuzzle.objects.create(
            game=self.user_game, name="Test Puzzle", grid_size=3,
            piece_positions=list(range(9)),
        )

    def test_games_view(self):
        response = self.client.get(reverse("game:games"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_main.html")
        titles = [g["title"] for g in response.context["games"]]
        self.assertIn("Звуковое лото", titles)

    def test_puzzle_game_view(self):
        self.assertEqual(self.client.get(reverse("game:puzzle_game")).status_code, 200)

    def test_memory_game_view(self):
        self.assertEqual(self.client.get(reverse("game:memory_game")).status_code, 200)

    def test_sound_loto_view(self):
        self.assertEqual(self.client.get(reverse("game:sound_loto")).status_code, 200)

    def test_whiteboard_view(self):
        self.assertEqual(self.client.get(reverse("game:whiteboard")).status_code, 200)

    def test_my_games_view_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("game:my_games")).status_code, 302)

    def test_my_games_view_shows_all_genres(self):
        self.create_memory_game()
        self.create_sound_loto()
        response = self.client.get(reverse("game:my_games"))
        self.assertEqual(response.status_code, 200)
        names = {g.display_name for g in response.context["user_games"]}
        self.assertTrue({"Test Puzzle", "Memory1", "SoundLoto1"} <= names)

    # --- Пазлы ---
    def test_save_puzzle_success(self):
        response = self.client.post(reverse("game:save_puzzle"), {
            "name": "New Puzzle", "gridSize": "3",
            "piecePositions": json.dumps(list(range(9))), "preset_image_path": "p.png",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserPuzzle.objects.filter(name="New Puzzle").exists())

    def test_save_puzzle_fail_empty_name(self):
        response = self.client.post(reverse("game:save_puzzle"), {
            "name": "", "gridSize": "3", "piecePositions": json.dumps(list(range(9))), "preset_image_path": "p.png",
        })
        self.assertEqual(response.status_code, 400)

    def test_load_puzzles_success(self):
        data = self.client.get(reverse("game:load_puzzles")).json()
        self.assertTrue(any(p["name"] == "Test Puzzle" for p in data["puzzles"]))

    def test_update_puzzle_success(self):
        url = reverse("game:update_puzzle", kwargs={"game_id": self.user_puzzle.game.game_id})
        content = encode_multipart(BOUNDARY, {
            "name": "Updated", "gridSize": "3",
            "piecePositions": json.dumps(list(range(9))), "preset_image_path": "p.png",
        })
        response = self.client.put(url, content, content_type=f"multipart/form-data; boundary={BOUNDARY}")
        self.assertEqual(response.status_code, 200)
        self.user_puzzle.refresh_from_db()
        self.assertEqual(self.user_puzzle.name, "Updated")

    # --- Поиск пар ---
    def test_save_memory_game_success(self):
        response = self.client.post(reverse("game:save_memory_game"), {
            "name": "New Memory", "pairCount": "2",
            "cardLayout": json.dumps([0, 1, 0, 1]), "presetName": "fruits",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.json())

    def test_save_memory_game_fail_no_source(self):
        response = self.client.post(reverse("game:save_memory_game"), {
            "name": "M", "pairCount": "2", "cardLayout": json.dumps([0, 1, 0, 1]),
        })
        self.assertEqual(response.status_code, 400)

    def test_load_memory_games_success(self):
        self.create_memory_game()
        data = self.client.get(reverse("game:load_memory_games")).json()
        self.assertTrue(any(g["name"] == "Memory1" for g in data["games"]))

    def test_update_memory_game_success(self):
        game = self.create_memory_game()
        url = reverse("game:update_memory_game", kwargs={"game_id": game.pk})
        content = encode_multipart(BOUNDARY, {
            "name": "Upd", "pairCount": "2", "cardLayout": json.dumps([1, 0, 1, 0]), "presetName": "animals",
        })
        response = self.client.put(url, content, content_type=f"multipart/form-data; boundary={BOUNDARY}")
        self.assertEqual(response.status_code, 200)
        game.refresh_from_db()
        self.assertEqual(game.name, "Upd")

    # --- Звуковое лото ---
    def test_save_sound_loto_success_with_preset(self):
        response = self.client.post(reverse("game:save_sound_loto"), {
            "name": "New SL", "roundsCount": "3", "cardsCount": "3", "presetName": "animals",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserSoundLoto.objects.filter(name="New SL").exists())

    def test_save_sound_loto_fail_no_source(self):
        response = self.client.post(reverse("game:save_sound_loto"), {
            "name": "S", "roundsCount": "3", "cardsCount": "3",
        })
        self.assertEqual(response.status_code, 400)

    def test_load_sound_lotos_success(self):
        self.create_sound_loto()
        data = self.client.get(reverse("game:load_sound_lotos")).json()
        self.assertTrue(any(g["name"] == "SoundLoto1" for g in data["games"]))

    def test_update_sound_loto_success(self):
        game = self.create_sound_loto()
        url = reverse("game:update_sound_loto", kwargs={"game_id": game.pk})
        content = encode_multipart(BOUNDARY, {
            "name": "Upd", "roundsCount": "4", "cardsCount": "4", "presetName": "transport",
        })
        response = self.client.put(url, content, content_type=f"multipart/form-data; boundary={BOUNDARY}")
        self.assertEqual(response.status_code, 200)
        game.refresh_from_db()
        self.assertEqual(game.rounds_count, 4)

    # --- Удаление ---
    def test_delete_game_success(self):
        game = self.create_sound_loto()
        response = self.client.delete(reverse("game:delete_game", kwargs={"game_id": game.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserGame.objects.filter(pk=game.pk).exists())

    def test_delete_game_not_found(self):
        response = self.client.delete(reverse("game:delete_game", kwargs={"game_id": "SLT-NOPE"}))
        self.assertEqual(response.status_code, 404)