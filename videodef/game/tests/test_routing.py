from django.test import SimpleTestCase

from game.routing import websocket_urlpatterns


class RoutingTest(SimpleTestCase):
    def test_routing_paths_exist(self):
        paths = [route.pattern.regex.pattern for route in websocket_urlpatterns]
        self.assertTrue(any("ws/puzzle_on_board/" in p for p in paths))
        self.assertTrue(any("ws/whiteboard/" in p for p in paths))
