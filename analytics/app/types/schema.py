from datetime import datetime
from typing import List, Optional
import strawberry


@strawberry.type
class SensorReadingType:
    id: int
    device_id: str
    sensor_type: str
    value: float
    unit: str
    recorded_at: datetime


@strawberry.type
class DeviceSummaryType:
    device_id: str
    sensor_type: str
    avg_value: float
    min_value: float
    max_value: float
    reading_count: int
    period_start: datetime
    period_end: datetime


@strawberry.type
class AlertSummaryType:
    total: int
    active: int
    critical: int
    warning: int


@strawberry.type
class DeviceType:
    id: str
    name: str
    device_type: str
    location: str
    is_active: bool
    created_at: datetime


@strawberry.type
class AlertType:
    id: str
    rule_id: str
    device_id: str
    triggered_value: float
    severity: str
    status: str
    created_at: datetime


@strawberry.type
class BucketedReadingType:
    bucket: datetime
    avg_value: float
    min_value: float
    max_value: float
    reading_count: int
