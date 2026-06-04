import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.models.alert import Alert, AlertRule
from app.notifier import send_alert_email
from app.ws_manager import manager

logger = logging.getLogger(__name__)

_OPERATORS = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
}


async def evaluate(message: dict, session_factory: async_sessionmaker) -> None:
    device_id = uuid.UUID(message["device_id"])
    sensor_type = message["sensor_type"]
    value = float(message["value"])
    recorded_at = message.get("recorded_at", datetime.now(timezone.utc).isoformat())

    async with session_factory() as session:
        rules = await _get_active_rules(session, device_id, sensor_type)

        for rule in rules:
            op_fn = _OPERATORS.get(rule.operator)
            if not (op_fn and op_fn(value, float(rule.threshold))):
                continue

            # Anti-tormenta: si ya existe una alerta abierta (activa o reconocida)
            # para esta regla, no se crea otra ni se reenvía correo.
            if await _has_open_alert(session, rule.id):
                continue

            alert = await _create_alert(session, rule, value)
            await session.commit()
            await session.refresh(alert)

            payload = {
                "event": "alert_triggered",
                "alert_id": str(alert.id),
                "device_id": str(alert.device_id),
                "sensor_type": sensor_type,
                "value": value,
                "threshold": float(rule.threshold),
                "operator": rule.operator,
                "severity": alert.severity,
                "recorded_at": recorded_at,
            }
            await manager.broadcast(payload)
            logger.warning(
                "ALERT %s — device=%s %s %s%s (threshold %s%s)",
                alert.severity.upper(), device_id, sensor_type,
                value, message.get("unit", ""),
                rule.operator, rule.threshold,
            )

            recipients = list(rule.notification_emails or []) or settings.alert_emails_list
            await send_alert_email(
                recipients,
                device_id=str(device_id),
                sensor_type=sensor_type,
                value=value,
                threshold=float(rule.threshold),
                operator=rule.operator,
                severity=alert.severity,
            )


async def _has_open_alert(session: AsyncSession, rule_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Alert.id)
        .where(Alert.rule_id == rule_id, Alert.status.in_(("active", "acknowledged")))
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _get_active_rules(
    session: AsyncSession, device_id: uuid.UUID, sensor_type: str
) -> list[AlertRule]:
    result = await session.execute(
        select(AlertRule).where(
            AlertRule.device_id == device_id,
            AlertRule.sensor_type == sensor_type,
            AlertRule.is_active == True,
        )
    )
    return result.scalars().all()


async def _create_alert(session: AsyncSession, rule: AlertRule, value: float) -> Alert:
    alert = Alert(
        rule_id=rule.id,
        device_id=rule.device_id,
        triggered_value=value,
        severity=rule.severity,
        status="active",
    )
    session.add(alert)
    await session.flush()
    return alert
