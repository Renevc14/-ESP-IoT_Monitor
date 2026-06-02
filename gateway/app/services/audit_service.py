"""Audit logging to security.audit_logs (OWASP A09 — Logging & Monitoring).

Uses a dedicated session that commits independently, so events are persisted
even when the originating request transaction is rolled back (e.g. a failed
login or a 403 that raises an HTTPException).
"""
import json
import logging

from fastapi import Request
from sqlalchemy import text

from app.db.database import AsyncSessionLocal

logger = logging.getLogger("audit")


def client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


async def log_event(
    action: str,
    *,
    user_id=None,
    resource: str | None = None,
    ip: str | None = None,
    details: dict | None = None,
) -> None:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "INSERT INTO security.audit_logs "
                    "(user_id, action, resource, ip_address, details) "
                    "VALUES (:user_id, :action, :resource, :ip, CAST(:details AS JSONB))"
                ),
                {
                    "user_id": str(user_id) if user_id else None,
                    "action": action,
                    "resource": resource,
                    "ip": ip,
                    "details": json.dumps(details) if details is not None else None,
                },
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to write audit log (action=%s)", action)
