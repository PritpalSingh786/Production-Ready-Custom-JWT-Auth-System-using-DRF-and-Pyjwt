# tasks.py
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
import json


@shared_task
def send_email_task(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list
    )


@shared_task
def send_new_login_alert_task(user_email, user_name, device_name, ip_address, platform, reset_token):
    """Send alert email when new login detected"""
    # Create reset link (using your domain)
    reset_link = f"{settings.DOMAIN_URL}/secure-password-change-template/{user_name}/{reset_token}/"
    
    subject = f"🔐 New Login Detected - {user_name}"
    
    message = f"""
    Hello {user_name},
    
    We detected a new login to your account:
    
    📱 Device: {device_name}
    🌍 IP Address: {ip_address}
    💻 Platform: {platform}
    🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    If this was NOT you, please click the link below within 3 minutes to secure your account:
    
    🔗 {reset_link}
    
    This link will expire in 3 minutes.
    
    If you did not request this, please ignore this email.
    
    Best regards,
    Your Team
    """
    
    send_email_task.delay(subject, message, [user_email])


@shared_task
def send_password_changed_email_task(user_email, user_name):
    """Send confirmation email after password change"""
    subject = "✅ Password Changed Successfully"
    
    message = f"""
    Hello {user_name},
    
    Your password has been successfully changed.
    
    You have been logged out from all devices for security reasons.
    
    If this was NOT you, please contact support immediately.
    
    Best regards,
    Your Team
    """
    
    send_email_task.delay(subject, message, [user_email])


@shared_task
def send_logout_notification_task(user_id, device_id, message):
    """Send WebSocket notification to specific device"""
    channel_layer = get_channel_layer()
    
    group_name = f"user_{user_id}_{device_id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "logout.notification",
            "message": message
        }
    )


@shared_task
def logout_all_devices_task(user_id, excluded_device_id=None):
    """Logout user from all devices (except optional excluded device)"""
    from .utils import redis_client
    
    user_tokens_key = f"hash-rt-for-user-{user_id}"
    
    # Get all tokens
    all_tokens = redis_client.hgetall(user_tokens_key)
    
    # Revoke all tokens
    redis_client.delete(user_tokens_key)
    
    # Send logout notification to all devices
    for jti, token_data_str in all_tokens.items():
        token_data = json.loads(token_data_str)
        device_id = token_data.get('device_id')
        
        # Skip excluded device if specified
        if excluded_device_id and device_id == excluded_device_id:
            continue
        
        if device_id:
            send_logout_notification_task.delay(
                user_id,
                device_id,
                "Your account password was changed. You have been logged out."
            )
    
    return len(all_tokens)