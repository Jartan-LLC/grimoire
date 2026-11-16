"""Send one email through the shop's SMTP server."""

import smtplib
from email.message import EmailMessage

from notifier import settings


def send(to: str, subject: str, body: str) -> None:
    """Send `body` to `to` with `subject`, from the shop's sender address."""
    message = EmailMessage()
    message["From"] = settings.SENDER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.send_message(message)
