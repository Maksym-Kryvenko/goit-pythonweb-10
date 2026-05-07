import logging
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import config

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    USE_CREDENTIALS=config.USE_CREDENTIALS,
    VALIDATE_CERTS=config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str):
    """Send an email verification link to the newly registered user.

    Generates a signed JWT and delivers it via the ``verify_email.html`` template.
    Connection errors are logged and swallowed so registration never fails silently.

    Args:
        email: Recipient email address.
        username: Display name included in the email body.
        host: Base URL of the service, used to build the verification link.
    """
    try:
        from src.services.auth import create_email_token

        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as e:
        logger.warning(f"Failed to connect while sending email: {e}")


async def send_reset_password_email(email: EmailStr, username: str, host: str):
    """Send a password-reset link to the user's email address.

    Generates a short-lived signed JWT and delivers it via the ``reset_password.html`` template.
    Connection errors are logged and swallowed.

    Args:
        email: Recipient email address.
        username: Display name included in the email body.
        host: Base URL of the service, used to build the reset link.
    """
    try:
        from src.services.auth import create_password_reset_token

        token_verification = await create_password_reset_token(email)
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as e:
        logger.warning(f"Failed to connect while sending email: {e}")
