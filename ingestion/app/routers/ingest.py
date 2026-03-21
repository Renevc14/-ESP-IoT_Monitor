import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import publisher
from app.config import settings
from app.schemas.reading import ReadingPayload, ReadingResponse

logger = logging.getLogger(__name__)
bearer = HTTPBearer()


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/reading", response_model=ReadingResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_reading(
    body: ReadingPayload,
    token_payload: dict = Depends(verify_jwt),
):
    message = {
        "device_id": str(body.device_id),
        "sensor_type": body.sensor_type.value,
        "value": body.value,
        "unit": body.unit,
        "recorded_at": body.recorded_at.isoformat(),
        "published_by": token_payload.get("sub"),
    }

    try:
        await publisher.publish(message)
    except Exception as exc:
        logger.error("Failed to publish reading: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        )

    return ReadingResponse(
        published=True,
        device_id=body.device_id,
        sensor_type=body.sensor_type.value,
        recorded_at=body.recorded_at,
    )
