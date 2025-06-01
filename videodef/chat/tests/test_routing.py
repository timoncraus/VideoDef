from django.test import SimpleTestCase
from chat import routing


class RoutingTest(SimpleTestCase):
    def test_websocket_urlpatterns(self):
        patterns = routing.websocket_urlpatterns
        self.assertTrue(
            any(
                pattern.pattern.regex.pattern == r"ws/chat/(?P<chat_id>\d+)/$"
                for pattern in patterns
            )
        )
