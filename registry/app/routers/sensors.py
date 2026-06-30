import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import require_operator
from app.models.sensor import Sensor
from app.schemas.sensor import SensorResponse

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("", response_model=list[SensorResponse])
async def list_sensors(
    device_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    query = select(Sensor).order_by(Sensor.device_id, Sensor.sensor_type)
    if device_id:
        query = query.where(Sensor.device_id == device_id)
    result = await db.execute(query)
    return result.scalars().all()
