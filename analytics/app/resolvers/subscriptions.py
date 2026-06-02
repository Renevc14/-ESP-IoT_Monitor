from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

import strawberry

from app.broadcaster import broadcaster
from app.types.schema import SensorReadingType


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def reading_added(
        self,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
    ) -> AsyncGenerator[SensorReadingType, None]:
        """Stream readings in real time as they are ingested (optionally filtered)."""
        queue = broadcaster.subscribe()
        try:
            while True:
                msg = await queue.get()
                if device_id and str(msg.get("device_id")) != device_id:
                    continue
                if sensor_type and msg.get("sensor_type") != sensor_type:
                    continue
                raw = msg.get("recorded_at")
                try:
                    recorded = datetime.fromisoformat(raw) if raw else datetime.now(timezone.utc)
                except (TypeError, ValueError):
                    recorded = datetime.now(timezone.utc)
                yield SensorReadingType(
                    id=0,
                    device_id=str(msg.get("device_id")),
                    sensor_type=str(msg.get("sensor_type")),
                    value=float(msg.get("value")),
                    unit=str(msg.get("unit", "")),
                    recorded_at=recorded,
                )
        finally:
            broadcaster.unsubscribe(queue)
