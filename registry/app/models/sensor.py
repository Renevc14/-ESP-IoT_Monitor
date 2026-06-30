import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Sensor(Base):
    """Catálogo de sensores expuestos por un dispositivo (entidad 'sensors')."""
    __tablename__ = "sensors"
    __table_args__ = {"schema": "iot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("iot.devices.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type: Mapped[str] = mapped_column(
        Enum(
            "temperature", "humidity", "energy",
            name="sensor_type", schema="iot", create_type=False,
        ),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
