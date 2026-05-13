import jwt
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import authentication, exceptions

from .redis_token_manager import redis_token_manager


User = get_user_model()


def verify_token(token, token_type="access"):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={
                "require": ["exp", "iat", "jti", "type"]
            }
        )

        if payload.get("type") != token_type:
            return None

        if redis_token_manager.is_blacklisted(payload.get("jti")):
            return None

        if payload["exp"] < datetime.utcnow().timestamp():
            return None

        user = User.objects.get(id=payload["user_id"])

        if not user.is_active:
            return None

        return payload

    except Exception:
        return None


class PyJWTAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]

        payload = verify_token(token, "access")

        if not payload:
            raise exceptions.AuthenticationFailed(
                "Invalid or expired token"
            )

        try:
            user = User.objects.get(id=payload["user_id"])

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "User not found"
            )

        request.device_id = payload.get("device_id")
        request.platform = payload.get("platform")

        return (user, token)