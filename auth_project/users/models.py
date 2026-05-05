from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=255)
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    last_login = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-last_login']

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"


class OutstandingToken(models.Model):
    """Stores all active refresh tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outstanding_tokens")
    token = models.TextField(unique=True)
    jti = models.CharField(max_length=100, unique=True, db_index=True)
    device_id = models.UUIDField(null=True, blank=True)
    platform = models.CharField(max_length=20, default="web")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_accessed = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
            models.Index(fields=['jti']),
            models.Index(fields=['user', 'is_active']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class BlacklistedToken(models.Model):
    """Stores blacklisted tokens by JTI"""
    jti = models.CharField(max_length=100, unique=True, db_index=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['blacklisted_at']),
            models.Index(fields=['jti']),
        ]

    def __str__(self):
        return f"Blacklisted JTI: {self.jti} - {self.reason}"