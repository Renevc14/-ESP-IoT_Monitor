import uuid
from datetime import datetime

from pydantic import BaseModel


class SensorResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    sensor_type: str
    unit: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
