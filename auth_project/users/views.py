from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)

from django.contrib.auth import get_user_model

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import (
    method_decorator
)

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
)

from .utils import verify_email_token, verify_password_reset_token, change_user_password
from .tasks import send_password_changed_email_task, logout_all_devices_task
from django.shortcuts import render
from django.views import View


User = get_user_model()

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


class VerifyEmailPageView(View):
    """Render email verification template"""
    
    def get(self, request):
        user_id = request.GET.get('user_id')
        token = request.GET.get('token')
        
        # Check if parameters are missing
        if not user_id or not token:
            return render(request, 'users/email_verification_error.html', {
                'message': 'Invalid verification link. Missing required parameters.'
            })
        
        # Get user
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return render(request, 'users/email_verification_error.html', {
                'message': 'User not found. The verification link may be invalid.'
            })
        
        # Verify Redis token
        is_valid, message = verify_email_token(user.id, token)
        
        if is_valid:
            # Activate user account
            user.email_verified = True
            user.is_active = True
            user.save()
            
            # Render success page
            return render(request, 'users/email_verification_success.html', {
                'user_id': user.user_id,
                'email': user.email
            })
        else:
            # Render error page
            return render(request, 'users/email_verification_error.html', {
                'message': message
            })


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
        platform = request.data.get("platform")

        if platform == "web":
            refresh_token = request.COOKIES.get(
                "refresh_token"
            )
        else:
            refresh_token = request.data.get(
                "refresh"
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

        tokens = serializer.save()

        response = Response(
            {
                "access": tokens["access"]
            },
            status=status.HTTP_200_OK
        )

        if platform == "web":
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh"],
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
                path="/api/users/"
            )
        else:
            response.data["refresh"] = (
                tokens["refresh"]
            )

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        platform = request.data.get("platform")

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
                "refresh": refresh_token
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.save()

        response = Response(
            data,
            status=status.HTTP_200_OK
        )

        if platform == "web":
            response.delete_cookie(
                key="refresh_token",
                path="/api/users/"
            )

        return response


class AuthenticatedView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "msg": (
                "Welcome to authenticated view"
            ),
            "user": {
                "id": request.user.id,
                "userId": (
                    request.user.user_id
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