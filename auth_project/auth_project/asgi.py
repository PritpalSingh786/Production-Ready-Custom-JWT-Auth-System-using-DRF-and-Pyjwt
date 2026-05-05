import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from users.websocketjwtmiddleware import JWTAuthMiddleware
import users.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            users.routing.websocket_urlpatterns
        )
    ),
})