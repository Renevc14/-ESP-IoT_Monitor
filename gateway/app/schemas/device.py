import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.device import AlertOperator, AlertSeverity, DeviceType, SensorType


# ── Devices ──────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceType
    location: str | None = None
    auth_token: str = Field(..., min_length=8, description="Raw token; will be bcrypt-hashed")


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    device_type: DeviceType
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


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


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    sensor_type: SensorType
    operator: AlertOperator
    threshold: float
    severity: AlertSeverity
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleUpdate(BaseModel):
    threshold: float | None = None
    severity: AlertSeverity | None = None
    is_active: bool | None = None
