from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    PasswordResetRequestView,
    SetNewPasswordView,
    ChangePasswordView,
    ProfileView,
    DevicesView,
    SessionsView,
    AuthenticatedView,
    PasswordResetPageView,
    PasswordResetConfirmView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/<str:uidb64>/<str:token>/", VerifyEmailView.as_view()),
    path("login/", LoginView.as_view()),
    path("token/refresh/", RefreshTokenView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("request-password-reset/", PasswordResetRequestView.as_view()),
    path("reset-password/", SetNewPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("devices/", DevicesView.as_view()),
    path("devices/<int:device_id>/", DevicesView.as_view()),
    path("sessions/", SessionsView.as_view()),
    path("authenticated/", AuthenticatedView.as_view()),
    path('reset-password/<str:user_id>/<str:token>/', 
         PasswordResetPageView.as_view(), 
         name='password_reset_page'),
    
    path('api/reset-password/', 
         PasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
]

"""

web: gunicorn rentNotify.wsgi
worker: celery -A auth_project worker --loglevel=info

"""
