from django.test import SimpleTestCase

from game.routing import websocket_urlpatterns


class RoutingTest(SimpleTestCase):
    def test_routing_paths_exist(self):
        paths = [route.pattern.regex.pattern for route in websocket_urlpatterns]
        self.assertTrue(any("ws/puzzle_on_board/" in p for p in paths))
        self.assertTrue(any("ws/memory_game_on_board/" in p for p in paths))
        self.assertTrue(any("ws/sound_loto_on_board/" in p for p in paths))
        self.assertTrue(any("ws/whiteboard/" in p for p in paths))

    def test_game_routes_capture_params(self):
        for fragment in ("puzzle_on_board", "memory_game_on_board", "sound_loto_on_board"):
            route = next(r for r in websocket_urlpatterns if fragment in r.pattern.regex.pattern)
            self.assertIn("board_room_name", route.pattern.regex.pattern)
            self.assertIn("game_id", route.pattern.regex.pattern)