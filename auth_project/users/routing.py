from django.urls import re_path
from .consumers import AuthConsumer

websocket_urlpatterns = [
    re_path(r'ws/auth/$', AuthConsumer.as_asgi()),
]