import jwt
import uuid
import json
import redis
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# Redis connection
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    retry_on_timeout=True,
    health_check_interval=30
)


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

        # Check blacklist (optional)
        if redis_client.get(f"blacklist:{payload.get('jti')}"):
            return None

        # Check expiration
        if payload["exp"] < datetime.utcnow().timestamp():
            return None

        # Check user exists
        user_exists = User.objects.filter(
            id=payload["user_id"],
            is_active=True
        ).exists()

        if not user_exists:
            return None

        return payload

    except jwt.ExpiredSignatureError:
        # Token expired - still return payload for cleanup
        try:
            # Decode without expiration validation
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={"verify_exp": False}
            )
            return payload
        except:
            return None
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
            redis_client.get
        )(f"blacklist:{payload.get('jti')}")

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

        # Store in Redis Hash
        user_tokens_key = f"hash-rt-for-user-{user.id}"
        
        token_data = {
            "jti": payload.get("jti"),
            "user_id": str(user.id),
            "device_id": str(device_id) if device_id else None,
            "platform": platform,
            "device_name": device_name,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat()
        }
        
        redis_client.hset(
            user_tokens_key,
            payload.get("jti"),
            json.dumps(token_data)
        )
        
        ttl_seconds = settings.REFRESH_TOKEN_LIFETIME * 24 * 60 * 60
        redis_client.expire(user_tokens_key, ttl_seconds)

        return True

    except Exception as e:
        print(f"Error storing token: {e}")
        return False
    

def generate_password_reset_token(user_id):
    token = secrets.token_urlsafe(32)

    redis_client.setex(
        f"pwd_reset:{user_id}",
        180,
        token
    )

    return token


def verify_password_reset_token(user_id, token):
    print(user_id, "uuuuuuuuu")
    print(token, "tttttttttt")
    """Verify if token is valid"""
    key = f"pwd_reset:{user_id}:{token}"
    stored_token = redis_client.get(key)
    print(stored_token, "sssss")
    
    if stored_token and stored_token == token:
        print("delete")
        # Delete token after verification (one-time use)
        redis_client.delete(key)
        return True
    
    return False


def change_user_password(user, new_password):
    """Change user password"""
    user.set_password(new_password)
    user.save()
    return True


def generate_verification_token(user_id):
    """
    Generate email verification token with 5 minutes expiry
    """
    token = secrets.token_urlsafe(32)
    key = f"email_verify:{user_id}:{token}"
    
    token_data = {
        "token": token,
        "user_id": str(user_id),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }
    
    # Store in Redis with 5 minutes expiry
    redis_client.setex(key, 300, json.dumps(token_data))
    
    return token

def verify_email_token(user_id, token):
    """
    Verify email verification token
    Returns: (is_valid, message)
    """
    key = f"email_verify:{user_id}:{token}"
    stored_data = redis_client.get(key)
    
    if stored_data:
        # Delete token after verification (one-time use)
        redis_client.delete(key)
        return True, "Email verified successfully"
    
    return False, "Verification link has expired (5 minutes) or is invalid"
