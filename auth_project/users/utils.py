import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import OutstandingToken, BlacklistedToken
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async

User = get_user_model()


async def averify_token(token, token_type='access'):
    """Verify and decode JWT token - Async version (for WebSocket)"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={'require': ['exp', 'iat', 'jti', 'type']}
        )
        
        if payload.get('type') != token_type:
            return None
        
        # Async database call
        exists = await sync_to_async(BlacklistedToken.objects.filter(jti=payload.get('jti')).exists)()
        if exists:
            return None
        
        if payload['exp'] < datetime.utcnow().timestamp():
            return None
        
        user_exists = await sync_to_async(User.objects.filter(id=payload['user_id'], is_active=True).exists)()
        if not user_exists:
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_access_token(user, device_id=None, platform="web"):
    """Create access token (15 minutes expiry)"""
    payload = {
        'user_id': user.id,
        'device_id': str(device_id) if device_id else None,
        'platform': platform,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'jti': str(uuid.uuid4())
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def create_refresh_token(user, device_id=None, platform="web"):
    """Create refresh token (7 days expiry)"""
    payload = {
        'user_id': user.id,
        'device_id': str(device_id) if device_id else None,
        'platform': platform,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'jti': str(uuid.uuid4())
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def is_token_blacklisted(jti):
    """Check if a token (by JTI) is blacklisted"""
    return BlacklistedToken.objects.filter(jti=jti).exists()


def blacklist_token(jti, reason=None):
    """Blacklist a token by its JTI"""
    BlacklistedToken.objects.create(
        jti=jti,
        reason=reason,
        blacklisted_at=datetime.utcnow()
    )
    return True


def blacklist_token_by_value(token_str, reason=None):
    """Blacklist token by its value (extract JTI first)"""
    try:
        # Decode without verification to get JTI
        payload = jwt.decode(
            token_str,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False}
        )
        jti = payload.get('jti')
        if jti:
            return blacklist_token(jti, reason)
    except:
        pass
    return False


def store_refresh_token(refresh_token_str, user, device_id=None, platform="web"):
    """Store refresh token in OutstandingToken table"""
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        
        OutstandingToken.objects.create(
            user=user,
            token=refresh_token_str,
            jti=payload.get('jti'),
            device_id=device_id,
            platform=platform,
            expires_at=datetime.fromtimestamp(payload['exp']),
            is_active=True
        )
        return True
    except Exception as e:
        print(f"Error storing token: {e}")
        return False


def get_active_tokens(user):
    """Get all active (non-blacklisted) tokens for user"""
    now = datetime.utcnow()
    
    active_outstanding = OutstandingToken.objects.filter(
        user=user,
        expires_at__gt=now,
        is_active=True
    )
    
    active_tokens = []
    for token in active_outstanding:
        if not is_token_blacklisted(token.jti):
            active_tokens.append(token)
    
    return active_tokens


def limit_user_sessions(user, max_sessions=5):
    """Limit number of active sessions"""
    active_tokens = get_active_tokens(user)
    
    if len(active_tokens) >= max_sessions:
        tokens_to_remove = active_tokens[max_sessions - 1:]
        channel_layer = get_channel_layer()
        
        for token_obj in tokens_to_remove:
            # Blacklist the token
            blacklist_token(token_obj.jti, reason="session_limit")
            
            # Mark as inactive
            token_obj.is_active = False
            token_obj.save()
            
            # Send WebSocket notification
            if token_obj.device_id and channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_{token_obj.device_id}",
                    {
                        "type": "session_killed",
                        "message": "Session limit exceeded. You have been logged out."
                    }
                )
        
        return len(tokens_to_remove)
    
    return 0


def clean_expired_tokens():
    """Delete expired tokens from database"""
    now = datetime.utcnow()
    
    expired = OutstandingToken.objects.filter(expires_at__lt=now)
    count = expired.count()
    
    # Delete blacklist entries for expired tokens
    for token in expired:
        BlacklistedToken.objects.filter(jti=token.jti).delete()
    
    # Delete expired tokens
    expired.delete()
    
    return count


def logout_from_device(user, device_id):
    """Logout from a specific device"""
    tokens = OutstandingToken.objects.filter(
        user=user, 
        device_id=device_id, 
        expires_at__gt=datetime.utcnow(),
        is_active=True
    )
    count = 0
    
    for token in tokens:
        blacklist_token(token.jti, reason="manual_logout_from_device")
        token.is_active = False
        token.save()
        count += 1
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}_{device_id}",
                {
                    "type": "session_killed",
                    "message": "You have been logged out from this device"
                }
            )
    
    return count


def refresh_access_token(refresh_token_str):
    """Generate new access token using refresh token"""
    from .pyjwtauthentication import verify_token  # Import here to avoid circular import
    
    payload = verify_token(refresh_token_str, 'refresh')
    
    if not payload:
        return None
    
    # Create new access token
    new_access = create_access_token(
        User.objects.get(id=payload['user_id']),
        payload.get('device_id'),
        payload.get('platform')
    )
    
    return new_access