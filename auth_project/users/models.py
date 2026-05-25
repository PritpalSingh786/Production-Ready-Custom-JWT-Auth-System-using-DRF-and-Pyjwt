# models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class CommonModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        self.is_deleted = True
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.save()


class UserManager(BaseUserManager):
    """Custom user manager for User model with email as unique identifier"""
    
    def create_user(self, email, user_id, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, user_id and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        if not user_id:
            raise ValueError('The User ID field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, user_id=user_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, user_id, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, user_id and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, user_id, password, **extra_fields)


class User(CommonModel, AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with alphanumeric userId (like prit123, hi123, john_doe)
    """
    # Alphanumeric userId - user chooses this (like username but we call it user_id)
    user_id = models.CharField(
        max_length=150, 
        unique=True, 
        db_index=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Use user_id for authentication? No, use email
    USERNAME_FIELD = 'email'
    # user_id will be required when creating user via createsuperuser
    REQUIRED_FIELDS = ['user_id', 'first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_id} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.user_id
    
    def get_short_name(self):
        return self.first_name or self.user_id


class Device(CommonModel):
    """
    Device model for tracking user devices/sessions.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="devices",
        db_index=True
    )
    device_name = models.CharField(max_length=255)
    device_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    last_login = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ["-last_login"]
        unique_together = ['user', 'device_name']
    
    def __str__(self):
        return f"{self.user.user_id} - {self.device_name}"
    
    def mark_inactive(self):
        self.is_active = False
        self.save()
    
    def activate(self):
        self.is_active = True
        self.save()