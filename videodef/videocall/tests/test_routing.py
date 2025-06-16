from django.test import SimpleTestCase

from videocall.routing import websocket_urlpatterns


class RoutingTest(SimpleTestCase):
    def test_routing_paths_exist(self):
        paths = [route.pattern.regex.pattern for route in websocket_urlpatterns]
        self.assertTrue(any("ws/videocall/" in p for p in paths))
        self.assertTrue(any("ws/notify/" in p for p in paths))
