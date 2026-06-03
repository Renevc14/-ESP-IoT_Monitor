import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.device import DeviceType


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceType
    location: str | None = None
    auth_token: str | None = Field(None, min_length=8, description="Opcional; si se omite se genera automáticamente")


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    device_type: DeviceType
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceCreatedResponse(DeviceResponse):
    auth_token: str  # token en claro, se devuelve una sola vez


class DeviceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    location: str | None = None
    is_active: bool | None = None
