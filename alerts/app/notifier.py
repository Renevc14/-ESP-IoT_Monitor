"""Email notification dispatch for alerts (HU-03).

Sends via SMTP (MailHog by default in local/dev). Best-effort: if SMTP is not
configured or unreachable, it logs and returns without raising, so alert
evaluation is never blocked by the notification channel.
"""
import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_alert_email(
    recipients: list[str],
    *,
    device_id: str,
    sensor_type: str,
    value: float,
    threshold: float,
    operator: str,
    severity: str,
) -> None:
    if not settings.smtp_host or not recipients:
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = f"[{severity.upper()}] Alerta de {sensor_type} en dispositivo {device_id}"
    message.set_content(
        f"Se detectó una lectura fuera de umbral.\n\n"
        f"Dispositivo: {device_id}\n"
        f"Sensor: {sensor_type}\n"
        f"Valor: {value}\n"
        f"Condición: {operator} {threshold}\n"
        f"Severidad: {severity}\n"
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            timeout=10,
        )
        logger.info("Alert email sent to %s", recipients)
    except Exception:
        logger.warning("Could not send alert email", exc_info=True)
