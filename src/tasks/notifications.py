import asyncio
from celery_conf import celery_app
from config import get_settings
from fastapi import Depends

from notifications import EmailSender
from notifications.interfaces import EmailSenderInterface


@celery_app.task(name="send_email_task")
def send_email_task(method_name: str, email: str, **kwargs):

    settings = get_settings()

    email_sender = EmailSender(
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        email=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=settings.SMTP_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
        purchase_successful_email_template_name=settings.PURCHASE_SUCCESSFUL_TEMPLATE_NAME,
    )

    func = getattr(email_sender, method_name, None)
    if not func:
        raise ValueError(f"{method_name} is not a valid EmailSender method")

    asyncio.run(func(email, **kwargs))