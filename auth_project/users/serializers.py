from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
# from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode
)
from django.utils.encoding import (
    force_bytes,
    force_str
)
from django.conf import settings

from .models import Device
from .tasks import send_email_task
from .utils import (
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    verify_token,
)
from .redis_token_manager import redis_token_manager

import datetime
import re
import uuid
from .tasks import send_new_login_alert_task
from .utils import generate_password_reset_token, generate_verification_token


User = get_user_model()

# token_generator = PasswordResetTokenGenerator()


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
    
    def send_verification_email(self, user):
        """
        Send verification email with 5 minutes expiry
        """
        try:
            # Generate Redis token (5 minutes expiry)
            token = generate_verification_token(user.id)
            
            # Create verification link for frontend
            verification_link = f"{settings.FRONTEND_URL}/verify-email?user_id={user.user_id}&token={token}"
            
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

    def save(self, **kwargs):
        """
        Save user and send verification email
        """
        user = self.create(self.validated_data)
        self.send_verification_email(user)
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
            raise serializers.ValidationError("Email not verified")

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

            print("start")
            
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
        print("hellooooooo")
        
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

    refresh = serializers.CharField(
        required=False
    )

    platform = serializers.CharField()

    def validate(self, attrs):

        refresh_token = attrs.get("refresh")

        if not refresh_token:
            raise serializers.ValidationError(
                "Refresh token required"
            )

        payload = verify_token(
            refresh_token,
            "refresh"
        )

        if not payload:
            raise serializers.ValidationError(
                "Invalid or expired refresh token"
            )

        attrs["payload"] = payload

        attrs["refresh_token"] = refresh_token

        return attrs

    def save(self):

        payload = self.validated_data["payload"]

        old_refresh_token = self.validated_data[
            "refresh_token"
        ]

        user = User.objects.get(
            id=payload["user_id"]
        )

        device_id = payload.get("device_id")

        platform = payload.get("platform")

        new_access = create_access_token(
            user,
            device_id,
            platform
        )

        new_refresh = create_refresh_token(
            user,
            device_id,
            platform
        )

        store_refresh_token(
            new_refresh,
            user,
            device_id,
            platform
        )

        return {
            "access": new_access,
            "refresh": new_refresh
        }


class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField(
        required=False
    )

    platform = serializers.CharField()

    all_devices = serializers.BooleanField(
        default=False
    )

    def validate(self, attrs):

        if (
            not attrs.get("refresh") and
            attrs.get("platform") != "web"
        ):
            if not attrs.get("all_devices"):
                raise serializers.ValidationError(
                    "Refresh token required"
                )

        return attrs

    def save(self, user, request):

        platform = self.validated_data["platform"]

        all_devices = self.validated_data.get(
            "all_devices",
            False
        )

        if all_devices:
            count = (
                redis_token_manager
                .revoke_all_user_tokens(
                    user.id,
                    "logout_all_devices"
                )
            )

            return {
                "msg": f"Logged out from {count} devices"
            }

        refresh_token = self.validated_data.get(
            "refresh"
        )

        if refresh_token:
            return {
                "msg": "Logged out successfully"
                }


class PasswordResetRequestSerializer(
    serializers.Serializer
):

    email = serializers.EmailField()

    def save(self):

        email = self.validated_data["email"]

        user = User.objects.filter(
            email=email
        ).first()

        if not user:
            return

        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        token = token_generator.make_token(user)

        expire = (
            datetime.datetime.utcnow() +
            datetime.timedelta(hours=2)
        )

        link = (
            f"{settings.FRONTEND_URL}"
            f"/reset-password/{uid}/{token}/"
        )

        send_email_task.delay(
            "Reset Password",
            f"Reset before {expire} UTC: {link}",
            [user.email]
        )


class SetNewPasswordSerializer(
    serializers.Serializer
):

    password = serializers.CharField(
        write_only=True
    )

    uidb64 = serializers.CharField()

    token = serializers.CharField()

    def validate(self, attrs):

        try:
            uid = force_str(
                urlsafe_base64_decode(
                    attrs["uidb64"]
                )
            )

            user = User.objects.get(pk=uid)

        except Exception:
            raise serializers.ValidationError(
                "Invalid link"
            )

        if not token_generator.check_token(
            user,
            attrs["token"]
        ):
            raise serializers.ValidationError(
                "Invalid or expired token"
            )

        attrs["user"] = user

        return attrs

    def save(self):

        user = self.validated_data["user"]

        user.set_password(
            self.validated_data["password"]
        )

        user.save()

        redis_token_manager.revoke_all_user_tokens(
            user.id,
            "password_changed"
        )


class ChangePasswordSerializer(
    serializers.Serializer
):

    old_password = serializers.CharField(
        write_only=True
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    def validate(self, attrs):

        user = self.context["request"].user

        if not user.check_password(
            attrs["old_password"]
        ):
            raise serializers.ValidationError({
                "old_password": "Wrong password"
            })

        return attrs

    def save(self):

        user = self.context["request"].user

        user.set_password(
            self.validated_data["new_password"]
        )

        user.save()

        redis_token_manager.revoke_all_user_tokens(
            user.id,
            "password_changed"
        )


class UserProfileSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "email_verified",
            "date_joined"
        ]

        read_only_fields = [
            "id",
            "email_verified",
            "date_joined"
        ]


class DeviceSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Device

        fields = [
            "id",
            "device_name",
            "device_id",
            "last_login",
            "ip_address"
        ]


class SessionSerializer(
    serializers.Serializer
):

    device_id = serializers.CharField()

    platform = serializers.CharField()

    created_at = serializers.CharField()

    device_name = serializers.CharField()

    def to_representation(self, instance):

        return {
            "device_id": instance.get(
                "device_id"
            ),
            "platform": instance.get(
                "platform"
            ),
            "device_name": instance.get(
                "device_name"
            ),
            "created_at": instance.get(
                "created_at"
            ),
            "ip_address": instance.get(
                "ip_address"
            )
        }