import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# Conjuntos válidos: una regla con valores fuera de estos se rechaza al crearse
# (antes se guardaba como texto libre y quedaba "muerta" sin disparar nunca).
SensorTypeLiteral = Literal["temperature", "humidity", "energy"]
OperatorLiteral = Literal["gt", "lt", "gte", "lte"]
SeverityLiteral = Literal["warning", "critical"]


class AlertRuleCreate(BaseModel):
    device_id: uuid.UUID
    sensor_type: SensorTypeLiteral
    operator: OperatorLiteral
    threshold: float
    severity: SeverityLiteral
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
    severity: SeverityLiteral | None = None
    notification_emails: list[str] | None = None
    is_active: bool | None = None
