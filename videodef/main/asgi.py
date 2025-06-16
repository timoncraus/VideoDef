import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

import chat.routing
import game.routing
import videocall.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns
                + game.routing.websocket_urlpatterns
                + videocall.routing.websocket_urlpatterns
            )
        ),
    }
)
