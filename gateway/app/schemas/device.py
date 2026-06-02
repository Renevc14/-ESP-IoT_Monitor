import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.device import AlertOperator, AlertSeverity, DeviceType, SensorType


# ── Devices ──────────────────────────────────────────────────────────────────

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
    # Token en claro: se devuelve UNA sola vez al crear el dispositivo
    auth_token: str


class DeviceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    location: str | None = None
    is_active: bool | None = None


# ── Alert Rules ───────────────────────────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    device_id: uuid.UUID
    sensor_type: SensorType
    operator: AlertOperator
    threshold: float
    severity: AlertSeverity
    notification_emails: list[str] = []


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    sensor_type: SensorType
    operator: AlertOperator
    threshold: float
    severity: AlertSeverity
    notification_emails: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleUpdate(BaseModel):
    threshold: float | None = None
    severity: AlertSeverity | None = None
    notification_emails: list[str] | None = None
    is_active: bool | None = None
