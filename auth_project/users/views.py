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

from .utils import verify_email_token, verify_password_reset_token, change_user_password
from .tasks import send_password_changed_email_task, logout_all_devices_task
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
import json


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
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response(
                {
                    "success": True,
                    "message": "Registration successful. Please check your email for verification link (expires in 5 minutes).",
                    "data": {
                        "user_id": user.user_id,
                        "email": user.email
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyEmailView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        token = request.query_params.get('token')
        
        if not user_id or not token:
            return Response(
                {"error": "user_id and token are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify Redis token
        is_valid, message = verify_email_token(user.id, token)
        
        if is_valid:
            user.email_verified = True
            user.is_active = True
            user.save()
            
            return Response({
                "success": True,
                "message": "Email verified successfully. You can now login."
            }, status=status.HTTP_200_OK)
        
        return Response(
            {
                "success": False, 
                "error": message,
                "expiry_minutes": 5
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendVerificationEmailView(APIView):
    """Resend verification email with new 5-minute token"""
    
    permission_classes = [AllowAny]
    
    @method_decorator(
        ratelimit(
            key="ip",
            rate="2/m",
            block=True
        )
    )
    def post(self, request):
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        
        if not user_id or not email:
            return Response(
                {"error": "user_id and email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id, email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found with provided credentials"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.email_verified:
            return Response(
                {"error": "Email already verified. Please login."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reuse serializer to send email
        serializer = RegisterSerializer()
        serializer.send_verification_email(user)
        
        return Response({
            "success": True,
            "message": "Verification email resent successfully. Valid for 5 minutes."
        }, status=status.HTTP_200_OK)


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
    

class PasswordResetPageView(View):
    """Render password reset template"""
    
    def get(self, request, user_id, token):
        # Verify token is valid
        if not verify_password_reset_token(user_id, token):
            return render(request, 'users/error.html', {
                'message': 'Invalid or expired link. Please request a new one.'
            })
        
        return render(request, 'users/reset_password.html', {
            'user_id': user_id,
            'token': token
        })


class PasswordResetConfirmView(APIView):
    """Handle password reset form submission"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("starttttttt")
        try:
            print("startttttttt")
            # Parse request data
            user_id = request.data.get('user_id')
            token = request.data.get('token')
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            # Validate all fields present
            if not all([user_id, token, current_password, new_password, confirm_password]):
                return Response({
                    'error': 'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate passwords match
            if new_password != confirm_password:
                return Response({
                    'error': 'New passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate password length
            if len(new_password) < 8:
                return Response({
                    'error': 'Password must be at least 8 characters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify current password
            if not user.check_password(current_password):
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Change password
            change_user_password(user, new_password)
            
            # Send email notification (async)
            send_password_changed_email_task.delay(
                user_email=user.email,
                user_name=user.user_id
            )
            
            # Logout from all devices (async)
            logout_all_devices_task.delay(user_id)
            
            return Response({
                'success': True,
                'message': 'Password changed successfully! You have been logged out from all devices.',
                'redirect': '/login/'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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