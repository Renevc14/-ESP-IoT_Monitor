import httpx
from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import require_viewer

router = APIRouter(prefix="/system", tags=["System"])

_SERVICES = {
    "ingestion": settings.ingestion_url,
    "processing": settings.processing_url,
    "alerts": settings.alerts_url,
    "analytics": settings.analytics_service_url,
}


@router.get("/health", dependencies=[Depends(require_viewer)])
async def services_health():
    out = [{"service": "gateway", "status": "healthy"}]
    async with httpx.AsyncClient(timeout=4.0) as client:
        for name, url in _SERVICES.items():
            try:
                resp = await client.get(f"{url}/health")
                resp.raise_for_status()
                out.append({"service": name, "status": "healthy"})
            except Exception:
                out.append({"service": name, "status": "down"})
    return out
