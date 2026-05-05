import jwt
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework import exceptions
from .utils import is_token_blacklisted

User = get_user_model()


def verify_token(token, token_type='access'):
    """
    Verify and decode JWT token
    Returns payload if valid, None otherwise
    """
    try:
        # Decode with strict validation
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={
                'require': ['exp', 'iat', 'jti', 'type']
            }
        )
        
        # Check token type
        if payload.get('type') != token_type:
            print(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
            return None
        
        # Check if token is blacklisted
        if is_token_blacklisted(payload.get('jti')):
            print("Token is blacklisted")
            return None
        
        # Check if token is expired
        if payload['exp'] < datetime.utcnow().timestamp():
            print("Token has expired")
            return None
        
        # Check if user exists
        try:
            user = User.objects.get(id=payload['user_id'])
            if not user.is_active:
                print("User is inactive")
                return None
        except User.DoesNotExist:
            print("User not found")
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None


class PyJWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT authentication using PyJWT for DRF"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        # Extract token (Bearer <token>)
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        
        # Verify token using verify_token function
        payload = verify_token(token, 'access')
        
        if not payload:
            raise exceptions.AuthenticationFailed('Invalid or expired token')
        
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        
        # Attach device_id and platform to request
        request.device_id = payload.get('device_id')
        request.platform = payload.get('platform')
        
        return (user, token)