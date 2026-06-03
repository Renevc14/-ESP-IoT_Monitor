import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DeviceType(str, enum.Enum):
    temperature_sensor = "temperature_sensor"
    humidity_sensor = "humidity_sensor"
    energy_meter = "energy_meter"
    multi_sensor = "multi_sensor"


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": "iot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(
            "temperature_sensor", "humidity_sensor", "energy_meter", "multi_sensor",
            name="device_type", schema="iot", create_type=False,
        ),
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(String(500))
    auth_token_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
