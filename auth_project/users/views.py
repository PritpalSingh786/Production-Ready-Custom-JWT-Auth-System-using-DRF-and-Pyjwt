from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views import View

from .serializers import (
    PasswordChangeSerializer,
    RegisterSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
    ForgotPasswordEmailSentSerializer,
    EmailVerificationSerializer,
    SecurePasswordChangeSerializer,
    SecurePasswordResetTokenValidationSerializer
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="3/m", block=True))
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
        
        # Validate using serializer
        serializer = EmailVerificationSerializer(data={
            "user_id": user_id,
            "token": token
        })
        
        if not serializer.is_valid():
            # Get the first error message
            error_message = list(serializer.errors.values())[0][0] if serializer.errors else "Verification failed"
            return render(request, 'users/email_verification_error.html', {
                'message': error_message
            })
        
        # Save and activate user
        result = serializer.save()
        user = result["user"]
        
        # Render success page
        return render(request, 'users/email_verification_success.html', {
            'user_id': user.user_id,
            'email': user.email
        })


class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
            response.data["refresh"] = data["refresh"]

        return response
    

class SecurePasswordChangeTemplatePageView(View):
    """Render password reset template"""
    
    def get(self, request, user_id, token):
        # Validate token using serializer
        serializer = SecurePasswordResetTokenValidationSerializer(data={
            "user_id": user_id,
            "token": token
        })
        
        if not serializer.is_valid():
            return render(request, 'users/error.html', {
                'message': 'Invalid or expired link. Please request a new one.'
            })
        
        return render(request, 'users/secure_password_change_template.html', {
            'user_id': user_id,
            'token': token
        })


class SecurePasswordChangeView(APIView):
    """Handle password reset form submission"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SecurePasswordChangeSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Return first error message
            error_message = list(serializer.errors.values())[0][0] if serializer.errors else "Validation failed"
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = serializer.save()
        
        return Response({
            'success': result['success'],
            'message': result['message'],
            'redirect': result['redirect']
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        platform = request.data.get("platform")

        if platform == "web":
            refresh_token = request.COOKIES.get("refresh_token")
        else:
            refresh_token = request.data.get("refresh")

        serializer = RefreshTokenSerializer(data={
            "refresh": refresh_token,
            "platform": platform
        })

        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()

        response = Response(
            {"access": tokens["access"]},
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
            response.data["refresh"] = tokens["refresh"]

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        platform = request.data.get("platform")

        if platform == "web":
            refresh_token = request.COOKIES.get("refresh_token")
        else:
            refresh_token = request.data.get("refresh")

        serializer = LogoutSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        response = Response(data, status=status.HTTP_200_OK)

        if platform == "web":
            response.delete_cookie(key="refresh_token", path="/api/users/")

        return response


class AuthenticatedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = User.objects.get(id=request.user.id)  # or user_id
            email = user.email
            userId = user.user_id
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        
        return Response({
            "msg": "Welcome to authenticated view",
            "user": {
                "id": request.user.id,
                "userId": userId,
                "email": email
            },
            "device_id": getattr(request, "device_id", None),
            "platform": getattr(request, "platform", None)
        })
    

class ForgotPasswordEmailSentAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordEmailSentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "success": True,
                "message": serializer.validated_data["message"]
            },
            status=200
        )
    

class PasswordChangeTemplatePageView(View):
    def get(self, request, user_id, token):
        # Using the existing verify_password_reset_token function since it's simple validation
        from .utils import verify_password_reset_token
        
        if not verify_password_reset_token(user_id, token):
            return render(
                request,
                "users/password_change_error.html",
                {
                    "message": "Invalid or expired link."
                }
            )

        return render(
            request,
            "users/password_change_template.html",
            {
                "user_id": user_id,
                "token": token
            }
        )
    

class PasswordChangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Password changed successfully. Now you can login."
            },
            status=status.HTTP_200_OK
        )