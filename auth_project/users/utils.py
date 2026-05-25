import jwt
import uuid

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model

from .redis_token_manager import redis_token_manager


User = get_user_model()


def create_access_token(
    user,
    device_id=None,
    platform="web"
):
    payload = {
        "user_id": str(user.id),
        "device_id": (
            str(device_id)
            if device_id else None
        ),
        "platform": platform,
        "type": "access",
        "exp": (
            datetime.utcnow() +
            timedelta(
                minutes=settings.ACCESS_TOKEN_LIFETIME
            )
        ),
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    user,
    device_id=None,
    platform="web"
):
    payload = {
        "user_id": str(user.id),
        "device_id": (
            str(device_id)
            if device_id else None
        ),
        "platform": platform,
        "type": "refresh",
        "exp": (
            datetime.utcnow() +
            timedelta(
                days=settings.REFRESH_TOKEN_LIFETIME
            )
        ),
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(
    token,
    token_type="access"
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "jti",
                    "type"
                ]
            }
        )

        if payload.get("type") != token_type:
            return None

        if redis_token_manager.is_blacklisted(
            payload.get("jti")
        ):
            return None

        if (
            payload["exp"] <
            datetime.utcnow().timestamp()
        ):
            return None

        user_exists = User.objects.filter(
            id=payload["user_id"],
            is_active=True
        ).exists()

        if not user_exists:
            return None

        return payload

    except Exception:
        return None


async def averify_token(
    token,
    token_type="access"
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "jti",
                    "type"
                ]
            }
        )

        if payload.get("type") != token_type:
            return None

        from asgiref.sync import sync_to_async

        is_blacklisted = await sync_to_async(
            redis_token_manager.is_blacklisted
        )(payload.get("jti"))

        if is_blacklisted:
            return None

        if (
            payload["exp"] <
            datetime.utcnow().timestamp()
        ):
            return None

        user_exists = await sync_to_async(
            User.objects.filter(
                id=payload["user_id"],
                is_active=True
            ).exists
        )()

        if not user_exists:
            return None

        return payload

    except Exception:
        return None


def store_refresh_token(
    refresh_token_str,
    user,
    device_id=None,
    platform="web",
    device_name="",
    ip_address=""
):
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )

        redis_token_manager.store_refresh_token(
            user_id=user.id,
            jti=payload.get("jti"),
            device_id=(
                str(device_id)
                if device_id else None
            ),
            platform=platform,
            device_name=device_name,
            ip_address=ip_address
        )

        return True

    except Exception as e:
        print(f"Error storing token: {e}")

        return False


def is_token_blacklisted(jti):

    return redis_token_manager.is_blacklisted(
        jti
    )


def blacklist_token(
    jti,
    reason=None
):
    return redis_token_manager.blacklist_token(
        jti,
        reason or "revoked"
    )


def blacklist_token_by_value(
    token_str,
    reason=None
):
    return (
        redis_token_manager
        .blacklist_token_by_value(
            token_str,
            reason or "revoked"
        )
    )


def get_active_tokens(user):

    return (
        redis_token_manager
        .get_user_active_tokens(user.id)
    )


def limit_user_sessions(
    user,
    max_sessions=5
):
    return (
        redis_token_manager
        .limit_user_sessions(
            user.id,
            max_sessions
        )
    )


def logout_from_device(
    user,
    device_id
):
    return (
        redis_token_manager
        .revoke_device_tokens(
            user.id,
            str(device_id),
            "manual_logout"
        )
    )


def revoke_all_user_tokens(
    user,
    reason="revoked_all"
):
    return (
        redis_token_manager
        .revoke_all_user_tokens(
            user.id,
            reason
        )
    )


def refresh_access_token(
    refresh_token_str
):
    payload = verify_token(
        refresh_token_str,
        "refresh"
    )

    if not payload:
        return None

    user = User.objects.get(
        id=payload["user_id"]
    )

    return create_access_token(
        user,
        payload.get("device_id"),
        payload.get("platform")
    )