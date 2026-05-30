from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailPageView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    AuthenticatedView,
    PasswordResetPageView,
    PasswordResetConfirmView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailPageView.as_view()),
    path("login/", LoginView.as_view()),
    path("token/refresh/", RefreshTokenView.as_view()),
    path("logout/", LogoutView.as_view()),
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
