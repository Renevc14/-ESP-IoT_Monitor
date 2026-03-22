import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    alert_rules: Mapped[list["AlertRule"]] = relationship(
        "AlertRule", back_populates="device", cascade="all, delete-orphan"
    )


class SensorType(str, enum.Enum):
    temperature = "temperature"
    humidity = "humidity"
    energy = "energy"


class AlertSeverity(str, enum.Enum):
    warning = "warning"
    critical = "critical"


class AlertOperator(str, enum.Enum):
    gt = "gt"
    lt = "lt"
    gte = "gte"
    lte = "lte"


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = {"schema": "alerts"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("iot.devices.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type: Mapped[str] = mapped_column(
        Enum("temperature", "humidity", "energy", name="sensor_type", schema="iot", create_type=False),
        nullable=False,
    )
    operator: Mapped[AlertOperator] = mapped_column(
        Enum(AlertOperator, schema="alerts", name="rule_operator", create_type=False),
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, schema="alerts", name="severity_level", create_type=False),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped["Device"] = relationship("Device", back_populates="alert_rules")
