import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


_sensor_type_enum = ENUM(
    "temperature", "humidity", "energy",
    name="sensor_type", schema="iot", create_type=False,
)
_severity_enum = ENUM(
    "warning", "critical",
    name="severity_level", schema="alerts", create_type=False,
)
_operator_enum = ENUM(
    "gt", "lt", "gte", "lte",
    name="rule_operator", schema="alerts", create_type=False,
)
_status_enum = ENUM(
    "active", "acknowledged", "resolved",
    name="alert_status", schema="alerts", create_type=False,
)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = {"schema": "alerts"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sensor_type: Mapped[str] = mapped_column(_sensor_type_enum, nullable=False)
    operator: Mapped[str] = mapped_column(_operator_enum, nullable=False)
    threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    severity: Mapped[str] = mapped_column(_severity_enum, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "alerts"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    triggered_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    severity: Mapped[str] = mapped_column(_severity_enum, nullable=False)
    status: Mapped[str] = mapped_column(_status_enum, nullable=False, default="active")
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
