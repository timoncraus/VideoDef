from django.test import Client
from django.urls import reverse
import json

from game.models import UserGame, UserPuzzle
from game.tests.utils import GameTestBase


class GameViewsTest(GameTestBase):
    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.login(username="user1", password="pass1234")

        self.user_game = UserGame.objects.create(
            user=self.user, genre=self.genre, game_id="testgame"
        )
        self.user_puzzle = UserPuzzle.objects.create(
            game=self.user_game,
            name="Test Puzzle",
            grid_size=3,
            piece_positions=[i for i in range(9)],
        )

    def test_games_view(self):
        url = reverse("game:games")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_main.html")
        self.assertIn("games", response.context)

    def test_puzzle_game_view(self):
        url = reverse("game:puzzle_game")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/puzzles.html")

    def test_whiteboard_view(self):
        url = reverse("game:whiteboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/whiteboard.html")

    def test_my_games_view_requires_login(self):
        self.client.logout()
        url = reverse("game:my_games")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # редирект на логин

    def test_my_games_view(self):
        url = reverse("game:my_games")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/my_games.html")
        self.assertIn("user_games", response.context)
        self.assertIn(self.user_game, response.context["user_games"])

    def test_save_puzzle_view_success_with_preset(self):
        url = reverse("game:save_puzzle")
        data = {
            "name": "New Puzzle",
            "gridSize": "2",
            "piecePositions": json.dumps([0, 1, 2, 3]),
            "preset_image_path": "preset1.png",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"status": "success", "message": 'Пазл "New Puzzle" успешно сохранен!'},
        )
        self.assertTrue(
            UserPuzzle.objects.filter(name="New Puzzle", grid_size=2).exists()
        )

    def test_save_puzzle_view_fail_empty_name(self):
        url = reverse("game:save_puzzle")
        data = {
            "name": "",
            "gridSize": "2",
            "piecePositions": json.dumps([0, 1, 2, 3]),
            "preset_image_path": "preset1.png",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Название не может быть пустым", response.json().get("message", "")
        )

    def test_save_puzzle_view_fail_invalid_grid_size(self):
        url = reverse("game:save_puzzle")
        data = {
            "name": "Puzzle",
            "gridSize": "1",
            "piecePositions": json.dumps([0]),
            "preset_image_path": "preset1.png",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Неверный или отсутствующий размер сетки",
            response.json().get("message", ""),
        )

    def test_save_puzzle_view_fail_piece_positions_length(self):
        url = reverse("game:save_puzzle")
        data = {
            "name": "Puzzle",
            "gridSize": "2",
            "piecePositions": json.dumps([0, 1]),  # должно быть 4
            "preset_image_path": "preset1.png",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Количество позиций", response.json().get("message", ""))

    def test_load_puzzles_view_success(self):
        url = reverse("game:load_puzzles")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(
            any(p["name"] == self.user_puzzle.name for p in data["puzzles"])
        )

    def test_update_puzzle_view_success(self):
        url = reverse(
            "game:update_puzzle", kwargs={"game_id": self.user_puzzle.game.pk}
        )
        # Для PUT-запроса с multipart/form-data сложнее, используем client.put с raw body
        from django.test.client import encode_multipart, BOUNDARY

        data = {
            "name": "Updated Puzzle",
            "gridSize": "3",
            "piecePositions": json.dumps([i for i in range(9)]),
            "preset_image_path": "preset_updated.png",
        }
        content = encode_multipart(BOUNDARY, data)
        response = self.client.put(
            url, content, content_type=f"multipart/form-data; boundary={BOUNDARY}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"status": "success", "message": 'Пазл "Updated Puzzle" успешно обновлен!'},
        )
        self.user_puzzle.refresh_from_db()
        self.assertEqual(self.user_puzzle.name, "Updated Puzzle")
