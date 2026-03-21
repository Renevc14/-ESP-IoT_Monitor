import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.alert import Alert
from app.ws_manager import manager

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)

router = APIRouter()


def _get_session_factory(request) -> async_sessionmaker:
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
        await session.commit()
        return {"id": str(alert.id), "status": alert.status}


@router.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; client can send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
