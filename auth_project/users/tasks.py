from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_email_task(
    subject,
    message,
    recipient_list
):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list
    )


@shared_task
def send_session_killed_email(email):

    subject = "Session Logged Out"

    message = (
        "Your account was logged in on another device, "
        "so one of your old sessions was logged out."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )