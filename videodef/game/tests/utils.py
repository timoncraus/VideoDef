from django.test import TestCase
from django.contrib.auth import get_user_model

from game.models import Genre, UserGame, UserPuzzle, UserMemoryGame, UserSoundLoto

User = get_user_model()


class GameTestBase(TestCase):
    """Базовый класс для тестов игр: создаёт пользователя, жанры и фабрики игр."""

    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass1234",
            phone_number="+7123456789",
        )

        self.genre = Genre.objects.create(code="PZL", name="Пазл")
        self.memory_genre = Genre.objects.create(code="MEM", name="Поиск пар")
        self.sound_loto_genre = Genre.objects.create(code="SLT", name="Звуковое лото")

    # --- Фабрики для всех жанров ---
    def create_user_game(self, genre=None):
        return UserGame.objects.create(user=self.user, genre=genre or self.genre)

    def create_puzzle(self, genre=None, **kwargs):
        defaults = dict(
            name="Puzzle1",
            grid_size=2,
            piece_positions=[1, 0, 3, 2],
            preset_image_path="images/british-cat.jpg",
        )
        defaults.update(kwargs)
        return UserPuzzle.objects.create(game=self.create_user_game(genre), **defaults)

    def create_memory_game(self, genre=None, **kwargs):
        defaults = dict(
            name="Memory1",
            pair_count=2,
            card_layout=[0, 1, 0, 1],
            preset_name="fruits",
        )
        defaults.update(kwargs)
        return UserMemoryGame.objects.create(game=self.create_user_game(genre or self.memory_genre), **defaults)

    def create_sound_loto(self, genre=None, **kwargs):
        defaults = dict(
            name="SoundLoto1",
            rounds_count=3,
            cards_count=3,
            preset_name="animals",
        )
        defaults.update(kwargs)
        return UserSoundLoto.objects.create(game=self.create_user_game(genre or self.sound_loto_genre), **defaults)