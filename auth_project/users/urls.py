from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailPageView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    AuthenticatedView,
    SecurePasswordChangeTemplatePageView,
    SecurePasswordChangeView,
    ForgotPasswordEmailSentAPIView, 
    PasswordChangeTemplatePageView,
    PasswordChangeView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailPageView.as_view()),
    path("login/", LoginView.as_view()),
    path('secure-password-change-template/<str:user_id>/<str:token>/', 
        SecurePasswordChangeTemplatePageView.as_view(), 
         name='secure-password-template'),
    path('secure-password-change/', 
         SecurePasswordChangeView.as_view(), 
         name='secure-password-change'),
    path("token/refresh/", RefreshTokenView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("authenticated/", AuthenticatedView.as_view()),
    path(
        "forgot-password/",
        ForgotPasswordEmailSentAPIView.as_view(),
        name="forgot-password"
    ),
    path(
        "password-change-template/<str:user_id>/<str:token>/",
        PasswordChangeTemplatePageView.as_view(),
        name="password-change-template"
    ),

    path(
        "password-change/",
        PasswordChangeView.as_view(),
        name="password-change"
    ),
]

"""

web: gunicorn rentNotify.wsgi
worker: celery -A auth_project worker --loglevel=info

"""
