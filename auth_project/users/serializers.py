from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
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
    limit_user_sessions,
    blacklist_token_by_value,
    get_active_tokens,
    refresh_access_token,
    verify_token,
    blacklist_token
)
from .redis_token_manager import redis_token_manager

import datetime
import re
import uuid


User = get_user_model()

token_generator = PasswordResetTokenGenerator()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_username(self, value):

        if len(value) < 4:
            raise serializers.ValidationError(
                "Username must be at least 4 characters long"
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError(
                "Username can contain only letters, numbers and underscore"
            )

        if User.objects.filter(
            username__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Username already exists"
            )

        return value

    
    def validate_email(self, value):
        
        email_regex = (
        r"^[a-zA-Z0-9._%+-]+"
        r"@[a-zA-Z0-9.-]+"
        r"\.[a-zA-Z]{2,}$"
        )
        if not re.match(email_regex, value):
            raise serializers.ValidationError(
                "Enter a valid email address"
                )
        if User.objects.filter(
            email__iexact=value
            ).exists():
            raise serializers.ValidationError(
            "Email already exists"
            )
        return value


    def save(self, **kwargs):

        user = User.objects.create_user(
            username=self.validated_data["username"],
            email=self.validated_data["email"],
            password=self.validated_data["password"]
        )

        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        token = token_generator.make_token(user)

        expire = (
            datetime.datetime.utcnow() +
            datetime.timedelta(hours=24)
        )

        link = (
            f"{settings.FRONTEND_URL}"
            f"/verify-email/{uid}/{token}/"
        )

        message = (
            f"Verify before {expire} UTC: {link}"
        )

        send_email_task.delay(
            "Verify Email",
            message,
            [user.email]
        )

        return user


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    platform = serializers.CharField()

    def validate(self, attrs):

        user = authenticate(
            username=attrs["username"],
            password=attrs["password"]
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid credentials"
            )

        if not user.email_verified:
            raise serializers.ValidationError(
                "Email not verified"
            )

        attrs["user"] = user

        return attrs

    def save(self, request):

        user = self.validated_data["user"]

        platform = self.validated_data["platform"]

        device_name = request.headers.get(
            "User-Agent",
            "Unknown"
        )

        device, created = Device.objects.get_or_create(
            user=user,
            device_name=device_name,
            defaults={
                "ip_address": request.META.get(
                    "REMOTE_ADDR"
                ),
                "device_id": uuid.uuid4()
            }
        )

        device.ip_address = request.META.get(
            "REMOTE_ADDR"
        )

        device.save()

        device_id = str(device.device_id)

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

        store_refresh_token(
            refresh_token,
            user,
            device_id,
            platform,
            device_name=device_name,
            ip_address=request.META.get(
                "REMOTE_ADDR"
            )
        )

        limit_user_sessions(
            user,
            max_sessions=5
        )

        return {
            "access": access_token,
            "refresh": refresh_token,
            "platform": platform,
            "user": {
                "id": user.id,
                "username": user.username,
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

        blacklist_token_by_value(
            old_refresh_token,
            reason="rotated"
        )

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
            blacklist_token_by_value(
                refresh_token,
                reason="logout"
            )

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

