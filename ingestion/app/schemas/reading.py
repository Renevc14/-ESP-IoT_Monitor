import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    energy = "energy"


class ReadingPayload(BaseModel):
    device_id: uuid.UUID
    sensor_type: SensorType
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., max_length=20)
    recorded_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.recorded_at is None:
            self.recorded_at = datetime.now(timezone.utc)


class ReadingResponse(BaseModel):
    published: bool
    device_id: uuid.UUID
    sensor_type: str
    recorded_at: datetime
