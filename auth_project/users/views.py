from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator
)

from django.utils.http import (
    urlsafe_base64_decode
)

from django.utils.encoding import force_str

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import (
    method_decorator
)

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    DeviceSerializer,
    SessionSerializer
)

from .models import Device

from .utils import (
    get_active_tokens,
    logout_from_device
)


User = get_user_model()

token_generator = PasswordResetTokenGenerator()


class RegisterView(APIView):

    permission_classes = [AllowAny]

    @method_decorator(
        ratelimit(
            key="ip",
            rate="3/m",
            block=True
        )
    )
    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "msg": (
                    "Registration successful. "
                    "Check your email."
                )
            },
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):

    permission_classes = [AllowAny]

    def get(
        self,
        request,
        uidb64,
        token
    ):
        try:
            uid = force_str(
                urlsafe_base64_decode(uidb64)
            )

            user = User.objects.get(pk=uid)

        except Exception:
            return Response(
                {"error": "Invalid link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if token_generator.check_token(
            user,
            token
        ):
            user.email_verified = True

            user.save()

            return Response({
                "msg": (
                    "Email verified successfully"
                )
            })

        return Response(
            {
                "error": (
                    "Invalid or expired token"
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):

    permission_classes = [AllowAny]

    @method_decorator(
        ratelimit(
            key="ip",
            rate="5/m",
            block=True
        )
    )
    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.save(request)

        response = Response({
            "access": data["access"],
            "user": data["user"]
        })

        if data["platform"] == "web":

            response.set_cookie(
                key="refresh_token",
                value=data["refresh"],
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
                path="/api/users/"
            )

        else:
            response.data["refresh"] = (
                data["refresh"]
            )

        return response


class RefreshTokenView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        platform = request.data.get(
            "platform"
        )

        if platform == "web":
            refresh_token = request.COOKIES.get(
                "refresh_token"
            )

        else:
            refresh_token = request.data.get(
                "refresh"
            )

        if not refresh_token:
            return Response(
                {
                    "error": (
                        "Refresh token required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefreshTokenSerializer(
            data={
                "refresh": refresh_token,
                "platform": platform
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.save()

        response = Response({
            "access": data["access"]
        })

        if platform == "web":

            response.set_cookie(
                key="refresh_token",
                value=data["refresh"],
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
                path="/api/users/"
            )

        else:
            response.data["refresh"] = (
                data["refresh"]
            )

        return response


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        platform = request.data.get(
            "platform",
            "web"
        )

        all_devices = request.data.get(
            "all_devices",
            False
        )

        if platform == "web":
            refresh_token = request.COOKIES.get(
                "refresh_token"
            )

        else:
            refresh_token = request.data.get(
                "refresh"
            )

        serializer = LogoutSerializer(
            data={
                "refresh": refresh_token,
                "platform": platform,
                "all_devices": all_devices
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = serializer.save(
            request.user,
            request
        )

        response = Response(result)

        if platform == "web":
            response.delete_cookie(
                "refresh_token",
                path="/api/users/"
            )

        return response


class PasswordResetRequestView(APIView):

    permission_classes = [AllowAny]

    @method_decorator(
        ratelimit(
            key="ip",
            rate="3/m",
            block=True
        )
    )
    def post(self, request):

        serializer = (
            PasswordResetRequestSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "msg": (
                    "If account exists, "
                    "email sent"
                )
            },
            status=status.HTTP_200_OK
        )


class SetNewPasswordView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = (
            SetNewPasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "msg": (
                    "Password reset successful"
                )
            },
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = (
            ChangePasswordSerializer(
                data=request.data,
                context={
                    "request": request
                }
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "msg": (
                    "Password changed "
                    "successfully. "
                    "Please login again."
                )
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = (
            UserProfileSerializer(
                request.user
            )
        )

        return Response(serializer.data)

    def put(self, request):

        serializer = (
            UserProfileSerializer(
                request.user,
                data=request.data,
                partial=True
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        if (
            "email" in serializer.validated_data
            and
            serializer.validated_data[
                "email"
            ] != request.user.email
        ):
            return Response(
                {
                    "error": (
                        "Email cannot be changed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(serializer.data)


class DevicesView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        devices = Device.objects.filter(
            user=request.user
        )

        serializer = DeviceSerializer(
            devices,
            many=True
        )

        return Response(serializer.data)

    def delete(
        self,
        request,
        device_id=None
    ):
        if device_id:

            try:
                device = Device.objects.get(
                    id=device_id,
                    user=request.user
                )

                logout_from_device(
                    request.user,
                    str(device.device_id)
                )

                device.delete()

                return Response({
                    "msg": "Device removed"
                })

            except Device.DoesNotExist:
                return Response(
                    {
                        "error": (
                            "Device not found"
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:
            current_device_id = getattr(
                request,
                "device_id",
                None
            )

            devices = Device.objects.filter(
                user=request.user
            )

            if current_device_id:
                devices = devices.exclude(
                    device_id=current_device_id
                )

            count = devices.count()

            for device in devices:
                logout_from_device(
                    request.user,
                    str(device.device_id)
                )

                device.delete()

            return Response({
                "msg": (
                    f"Removed {count} "
                    f"other devices"
                )
            })


class SessionsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        sessions = get_active_tokens(
            request.user
        )

        serializer = SessionSerializer(
            sessions,
            many=True
        )

        return Response(serializer.data)


class AuthenticatedView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "msg": (
                "Welcome to authenticated view"
            ),
            "user": {
                "id": request.user.id,
                "username": (
                    request.user.username
                ),
                "email": request.user.email
            },
            "device_id": getattr(
                request,
                "device_id",
                None
            ),
            "platform": getattr(
                request,
                "platform",
                None
            )
        })