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
        ordering = ["-last_login"]

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
