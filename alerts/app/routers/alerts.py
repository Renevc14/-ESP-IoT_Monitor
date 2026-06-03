import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.models.alert import Alert
from app.ws_manager import manager

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)

router = APIRouter()


def _get_session_factory(request: Request) -> async_sessionmaker:
    return request.app.state.session_factory


@router.get("/alerts", tags=["Alerts"])
async def list_alerts(
    status: str | None = None,
    limit: int = 50,
    session_factory: async_sessionmaker = Depends(_get_session_factory),
):
    async with session_factory() as session:
        query = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
        if status:
            query = query.where(Alert.status == status)
        result = await session.execute(query)
        alerts = result.scalars().all()
        return [
            {
                "id": str(a.id),
                "device_id": str(a.device_id),
                "severity": a.severity,
                "status": a.status,
                "triggered_value": float(a.triggered_value),
                "created_at": a.created_at.isoformat(),
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ]


@router.patch("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(
    alert_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session_factory: async_sessionmaker = Depends(_get_session_factory),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")

    async with session_factory() as session:
        result = await session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if alert.status != "active":
            raise HTTPException(status_code=409, detail=f"Alert is already {alert.status}")

        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        await session.commit()
        return {"id": str(alert.id), "status": alert.status}


@router.patch("/alerts/{alert_id}/resolve", tags=["Alerts"])
async def resolve_alert(
    alert_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session_factory: async_sessionmaker = Depends(_get_session_factory),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")

    async with session_factory() as session:
        result = await session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if alert.status == "resolved":
            raise HTTPException(status_code=409, detail="Alert is already resolved")

        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        await session.commit()
        return {"id": str(alert.id), "status": alert.status}


def _valid_access_token(token: str | None) -> bool:
    if not token or not settings.jwt_secret_key:
        return False
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"]).get("type") == "access"
    except JWTError:
        return False


@router.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket, token: str | None = Query(default=None)):
    # El navegador no puede enviar headers en WebSocket: el access token llega como
    # query param y se valida antes de aceptar la conexión.
    if not _valid_access_token(token):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # mantiene viva la conexión
    except WebSocketDisconnect:
        manager.disconnect(ws)
