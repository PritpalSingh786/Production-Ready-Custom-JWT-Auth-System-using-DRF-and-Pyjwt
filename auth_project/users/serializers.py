from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Device
from .tasks import send_email_task, send_password_changed_email_task, logout_all_devices_task
from .utils import (
    create_access_token,
    create_refresh_token,
    delete_secure_password_reset_token,
    store_refresh_token,
    decode_token,
    verify_email_token,
    secure_verify_password_reset_token,
    change_user_password,
    secure_generate_password_reset_token,
    generate_verification_token,
    generate_password_reset_token,
    verify_password_reset_token,
    delete_password_reset_token,
    delete_verify_email_token
)
from datetime import datetime, timedelta
import re
import uuid
from .tasks import send_new_login_alert_task, send_forgot_password_email_task
import json
from django.conf import settings

redis_client = settings.REDIS_CLIENT

User = get_user_model()


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
        expire = datetime.utcnow() + timedelta(minutes=5)
        
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
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["user_id", "email", "password"]

    def validate_user_id(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("userId must be at least 4 characters long")

        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError("userId can contain only letters, numbers and underscore")

        if User.objects.filter(user_id__iexact=value).exists():
            raise serializers.ValidationError("userId already exists")

        return value
    
    def validate_email(self, value):
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
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
            user = User.objects.create_user(
                user_id=validated_data["user_id"],
                email=validated_data["email"],
                password=validated_data["password"],
                is_active=False,
                email_verified=False
            )
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Error creating user: {str(e)}")

    def save(self, **kwargs):
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
            reset_token = secure_generate_password_reset_token(user.id)
            send_new_login_alert_task.delay(
                user_email=user.email,
                id=user.id,
                userId=user.user_id,
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
            raise serializers.ValidationError("Invalid or expired refresh token")

        user_id = payload.get("user_id")
        jti = payload.get("jti")

        redis_key = f"hash-rt-for-user-{user_id}"

        token_data = redis_client.hget(redis_key, jti)

        if not token_data:
            raise serializers.ValidationError("Session expired. Please login again.")

        token_info = json.loads(token_data)

        created_at = datetime.fromisoformat(token_info["created_at"])

        token_age = (datetime.utcnow() - created_at).days

        if token_age >= settings.REFRESH_TOKEN_LIFETIME:
            redis_client.hdel(redis_key, jti)
            raise serializers.ValidationError("Session expired. Please login again.")

        attrs["payload"] = payload
        attrs["redis_key"] = redis_key
        attrs["old_jti"] = jti

        return attrs

    def save(self):
        payload = self.validated_data["payload"]
        redis_key = self.validated_data["redis_key"]
        old_jti = self.validated_data["old_jti"]

        user = User.objects.get(id=payload["user_id"])
        device_id = payload.get("device_id")
        platform = payload.get("platform")

        # Remove old refresh token
        redis_client.hdel(redis_key, old_jti)

        # Create new tokens
        access_token = create_access_token(user, device_id, platform)
        refresh_token = create_refresh_token(user, device_id, platform)

        # Save new refresh token
        store_refresh_token(refresh_token, user, device_id, platform)

        return {
            "access": access_token,
            "refresh": refresh_token
        }
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh")

        if not refresh_token:
            raise serializers.ValidationError("Refresh token required")

        payload = decode_token(refresh_token, "refresh")

        if not payload:
            raise serializers.ValidationError("Invalid or expired refresh token")

        user_id = payload.get("user_id")
        jti = payload.get("jti")

        redis_key = f"hash-rt-for-user-{user_id}"

        token_data = redis_client.hget(redis_key, jti)

        if not token_data:
            raise serializers.ValidationError("Session already expired")

        attrs["redis_key"] = redis_key
        attrs["jti"] = jti

        return attrs

    def save(self):
        redis_client.hdel(self.validated_data["redis_key"], self.validated_data["jti"])
        return {"message": "Logout successful"}
    

class ForgotPasswordEmailSentSerializer(serializers.Serializer):
    userId = serializers.CharField()

    def validate(self, attrs):
        user_id = attrs.get("userId")

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"userId": "Invalid User ID."})

        token = generate_password_reset_token(user.id)
        reset_link = f"{settings.DOMAIN_URL}/password-change-template/{user.id}/{token}/"

        expire = datetime.utcnow() + timedelta(minutes=5)

        message = f"""
        Hello {user.user_id},

        We received a request to reset your password.

        Click the link below to reset it:

        🔗 {reset_link}

        This link will expire in 5 minutes.

        Expiry Time:
        {expire.strftime('%H:%M:%S UTC')}

        If you did not request a password reset,
        please ignore this email.

        Regards,
        Your Team
        """

        send_forgot_password_email_task.delay(
            "Reset Your Password",
            message,
            [user.email]
        )

        attrs["message"] = "Password reset link sent successfully."
        return attrs
    

class PasswordChangeSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        token = attrs.get("token")

        if not verify_password_reset_token(user_id, token):
            raise serializers.ValidationError("Invalid or expired link.")

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        token = self.validated_data["token"]

        user.set_password(self.validated_data["new_password"])
        user.save()

        delete_password_reset_token(user.id, token)
        return user


class EmailVerificationSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        token = attrs.get("token")

        # Check if parameters are missing
        if not user_id or not token:
            raise serializers.ValidationError("Invalid verification link. Missing required parameters.")

        # Get user
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found. The verification link may be invalid.")

        # Verify Redis token
        is_valid, message = verify_email_token(user.id, token)

        if not is_valid:
            raise serializers.ValidationError(message)

        attrs["user"] = user
        attrs["message"] = message
        return attrs

    def save(self):
        user = self.validated_data["user"]
        token = self.validated_data["token"]
        
        # Activate user account
        user.email_verified = True
        user.is_active = True
        user.save()
        delete_verify_email_token(user.id, token)
        
        return {
            "user": user,
            "message": "Email verified successfully"
        }


class SecurePasswordChangeSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        token = attrs.get("token")
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # Validate all fields present
        if not all([user_id, token, current_password, new_password, confirm_password]):
            raise serializers.ValidationError("All fields are required")

        # Validate passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
        
        if not secure_verify_password_reset_token(user_id, token):
            raise serializers.ValidationError("Invalid or expired link.")

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Verify current password
        if not user.check_password(current_password):
            raise serializers.ValidationError({"current_password": "Current password is incorrect"})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        token = self.validated_data["token"]
        new_password = self.validated_data["new_password"]
        
        # Change password
        change_user_password(user, new_password)
        
        # Send email notification (async)
        send_password_changed_email_task.delay(
            user_email=user.email,
            user_name=user.user_id
        )
        
        # Logout from all devices (async)
        logout_all_devices_task.delay(user.id)

        delete_secure_password_reset_token(user.id, token)
        
        return {
            "success": True,
            "message": "Password changed successfully! You have been logged out from all devices.",
            "redirect": "/login/"
        }


class SecurePasswordResetTokenValidationSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        token = attrs.get("token")

        if not secure_verify_password_reset_token(user_id, token):
            raise serializers.ValidationError("Invalid or expired link. Please request a new one.")

        return attrs