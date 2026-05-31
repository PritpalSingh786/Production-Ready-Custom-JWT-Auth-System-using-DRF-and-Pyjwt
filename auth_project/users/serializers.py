from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Device
from .tasks import send_email_task
from .utils import (
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    decode_token
)
from datetime import datetime
import re
import uuid
from .tasks import send_new_login_alert_task
from .utils import generate_password_reset_token, generate_verification_token
import json
from django.conf import settings

redis_client = settings.REDIS_CLIENT


User = get_user_model()

# token_generator = PasswordResetTokenGenerator()


def send_verification_email(user):
    """
    Send verification email with 5 minutes expiry
    
    Args:
        user: User object with user_id, email, and id attributes
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate Redis token (5 minutes expiry)
        token = generate_verification_token(user.id)
        
        # Create verification link for frontend
        verification_link = f"{settings.DOMAIN_URL}/verify-email?user_id={user.user_id}&token={token}"
        
        # Expiry time for email
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        
        message = f"""
        Hello {user.user_id},

        Thank you for registering!

        Please verify your email address by clicking the link below:

        🔗 {verification_link}

        ⏰ This link will expire in 5 minutes (at {expire.strftime('%H:%M:%S UTC')}).

        If you did not create this account, please ignore this email.

        Best regards,
        Your Team
        """
        
        # Send email asynchronously
        send_email_task.delay(
            "Verify Your Email - 5 Minutes Expiry",
            message,
            [user.email]
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User
        fields = ["user_id", "email", "password"]

    def validate_user_id(self, value):
        if len(value) < 4:
            raise serializers.ValidationError(
                "userId must be at least 4 characters long"
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError(
                "userId can contain only letters, numbers and underscore"
            )

        if User.objects.filter(user_id__iexact=value).exists():
            raise serializers.ValidationError("userId already exists")

        return value
    
    def validate_email(self, value):
        email_regex = (
            r"^[a-zA-Z0-9._%+-]+"
            r"@[a-zA-Z0-9.-]+"
            r"\.[a-zA-Z]{2,}$"
        )
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Enter a valid email address")
            
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")
            
        return value

    def create(self, validated_data):
        """
        Create user with email verification
        """
        try:
            # Create user (inactive until email verified)
            user = User.objects.create_user(
                user_id=validated_data["user_id"],
                email=validated_data["email"],
                password=validated_data["password"],
                is_active=False,
                email_verified=False
            )
            
            return user
            
        except Exception as e:
            raise serializers.ValidationError(
                f"Error creating user: {str(e)}"
            )

    def save(self, **kwargs):
        """
        Save user and send verification email
        """
        user = self.create(self.validated_data)
        send_verification_email(user)
        return user

class LoginSerializer(serializers.Serializer):
    userId = serializers.CharField()
    password = serializers.CharField(write_only=True)
    platform = serializers.CharField()

    def validate(self, attrs):
        try:
            user = User.objects.get(user_id=attrs["userId"])
            if not user.check_password(attrs["password"]):
                raise User.DoesNotExist
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.email_verified:
            send_verification_email(user)
            raise serializers.ValidationError("Email not verified. A verification link has been sent to your email. Please verify your email before logging in.")
        attrs["user"] = user
        return attrs

    def save(self, request):
        user = self.validated_data["user"]
        platform = self.validated_data["platform"]
        
        # Get device name
        device_name = request.headers.get("User-Agent", "Unknown")
        
        # Get real IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Check if device already exists
        device, created = Device.objects.get_or_create(
            user=user,
            device_name=device_name,
            defaults={
                "ip_address": ip_address,
                "device_id": uuid.uuid4()
            }
        )
        
        # Update IP address
        device.ip_address = ip_address
        device.save()
        device_id = str(device.device_id)
        
        # Send alert if new device/login
        if device:
            # Generate password reset token (expires in 3 minutes)
            reset_token = generate_password_reset_token(user.id)
            # Send email asynchronously
            send_new_login_alert_task.delay(
                user_email=user.email,
                user_name=user.id,
                device_name=device_name,
                ip_address=ip_address,
                platform=platform,
                reset_token=reset_token
            )
        
        # Create tokens
        access_token = create_access_token(user, device_id, platform)
        refresh_token = create_refresh_token(user, device_id, platform)
        
        # Store refresh token
        store_refresh_token(
            refresh_token,
            user,
            device_id,
            platform,
            device_name=device_name,
            ip_address=ip_address
        )
        
        return {
            "access": access_token,
            "refresh": refresh_token,
            "platform": platform,
            "user": {
                "id": user.id,
                "userId": user.user_id,
                "email": user.email
            }
        }


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    platform = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs["refresh"]

        payload = decode_token(refresh_token, "refresh")

        if not payload:
            raise serializers.ValidationError(
                "Invalid or expired refresh token"
            )

        user_id = payload.get("user_id")
        jti = payload.get("jti")

        redis_key = f"hash-rt-for-user-{user_id}"

        token_data = redis_client.hget(redis_key, jti)

        if not token_data:
            raise serializers.ValidationError(
                "Session expired. Please login again."
            )

        token_info = json.loads(token_data)

        created_at = datetime.fromisoformat(
            token_info["created_at"]
        )

        token_age = (
            datetime.utcnow() - created_at
        ).days

        if token_age >= settings.REFRESH_TOKEN_LIFETIME:
            redis_client.hdel(redis_key, jti)

            raise serializers.ValidationError(
                "Session expired. Please login again."
            )

        attrs["payload"] = payload
        attrs["redis_key"] = redis_key
        attrs["old_jti"] = jti

        return attrs

    def save(self):
        payload = self.validated_data["payload"]
        redis_key = self.validated_data["redis_key"]
        old_jti = self.validated_data["old_jti"]

        user = User.objects.get(
            id=payload["user_id"]
        )

        device_id = payload.get("device_id")
        platform = payload.get("platform")

        # Remove old refresh token
        redis_client.hdel(redis_key, old_jti)

        # Create new tokens
        access_token = create_access_token(
            user,
            device_id,
            platform
        )

        refresh_token = create_refresh_token(
            user,
            device_id,
            platform
        )

        # Save new refresh token
        store_refresh_token(
            refresh_token,
            user,
            device_id,
            platform
        )

        return {
            "access": access_token,
            "refresh": refresh_token
        }
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh")

        if not refresh_token:
            raise serializers.ValidationError(
                "Refresh token required"
            )

        payload = decode_token(
            refresh_token,
            "refresh"
        )

        if not payload:
            raise serializers.ValidationError(
                "Invalid or expired refresh token"
            )

        user_id = payload.get("user_id")
        jti = payload.get("jti")

        redis_key = (
            f"hash-rt-for-user-{user_id}"
        )

        token_data = redis_client.hget(
            redis_key,
            jti
        )

        if not token_data:
            raise serializers.ValidationError(
                "Session already expired"
            )

        attrs["redis_key"] = redis_key
        attrs["jti"] = jti

        return attrs

    def save(self):
        redis_client.hdel(
            self.validated_data["redis_key"],
            self.validated_data["jti"]
        )

        return {
            "message": "Logout successful"
        }


