"""Transparent HTTP proxy to the alerts service."""
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
async def list_alerts(
    status: str | None = Query(None),
    limit: int = Query(50),
    _=Depends(get_current_user),
):
    params = {"limit": limit}
    if status:
        params["status"] = status
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{settings.alerts_url}/alerts", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Alerts service unavailable: {exc}")


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: uuid.UUID,
    request: Request,
    _=Depends(get_current_user),
):
    token = request.headers.get("Authorization", "")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.patch(
                f"{settings.alerts_url}/alerts/{alert_id}/acknowledge",
                headers={"Authorization": token},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Alerts service unavailable: {exc}")
