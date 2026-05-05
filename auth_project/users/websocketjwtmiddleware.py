import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from asgiref.sync import sync_to_async
from .models import User
from .pyjwtauthentication import verify_token


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        token = None

        if "token=" in query_string:
            token = query_string.split("token=")[1].split("&")[0]

        scope["user"] = AnonymousUser()
        scope["device_id"] = None

        if token:
            try:
                # Verify token using verify_token function
                payload = verify_token(token, 'access')
                
                if payload:
                    user = await sync_to_async(User.objects.get)(id=payload["user_id"])
                    scope["user"] = user
                    scope["device_id"] = payload.get("device_id")
                    
            except Exception as e:
                print(f"WebSocket auth error: {e}")

        return await super().__call__(scope, receive, send)