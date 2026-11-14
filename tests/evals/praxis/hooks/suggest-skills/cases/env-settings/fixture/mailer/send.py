"""Hand a message to the SMTP server."""

import smtplib
from email.message import EmailMessage

from mailer.config import load


def send(message: EmailMessage) -> None:
    """Send `message` through the configured server."""
    settings = load()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.timeout_s) as smtp:
        smtp.set_debuglevel(1 if settings.debug else 0)
        smtp.send_message(message)
