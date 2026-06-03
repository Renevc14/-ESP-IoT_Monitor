import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertRuleCreate(BaseModel):
    device_id: uuid.UUID
    sensor_type: str
    operator: str
    threshold: float
    severity: str
    notification_emails: list[str] = []


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    sensor_type: str
    operator: str
    threshold: float
    severity: str
    notification_emails: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleUpdate(BaseModel):
    threshold: float | None = None
    severity: str | None = None
    notification_emails: list[str] | None = None
    is_active: bool | None = None
