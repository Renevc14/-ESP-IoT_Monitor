"""Best-effort SMTP mailer for the gateway (password recovery)."""
import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        logger.info("SMTP no configurado; email omitido (%s)", subject)
        return
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        await aiosmtplib.send(message, hostname=settings.smtp_host, port=settings.smtp_port, timeout=10)
        logger.info("Email enviado a %s", to)
    except Exception:
        logger.warning("No se pudo enviar email a %s", to, exc_info=True)
