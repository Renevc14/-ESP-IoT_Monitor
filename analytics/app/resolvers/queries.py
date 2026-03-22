from datetime import datetime, timedelta, timezone
from typing import List, Optional

import strawberry
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.types.schema import AlertSummaryType, AlertType, DeviceSummaryType, DeviceType, SensorReadingType


async def resolve_readings(
    info: strawberry.types.Info,
    device_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    limit: int = 100,
) -> List[SensorReadingType]:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        query = "SELECT id, device_id, sensor_type, value, unit, recorded_at FROM iot.sensor_readings"
        conditions, params = [], {}

        if device_id:
            conditions.append("device_id = :device_id")
            params["device_id"] = device_id
        if sensor_type:
            conditions.append("sensor_type = :sensor_type")
            params["sensor_type"] = sensor_type

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY recorded_at DESC LIMIT :limit"
        params["limit"] = limit

        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [
            SensorReadingType(
                id=r[0],
                device_id=str(r[1]),
                sensor_type=r[2],
                value=float(r[3]),
                unit=r[4],
                recorded_at=r[5],
            )
            for r in rows
        ]


async def resolve_device_summary(
    info: strawberry.types.Info,
    device_id: str,
    hours: int = 24,
) -> List[DeviceSummaryType]:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await session.execute(
            text("""
                SELECT
                    device_id,
                    sensor_type,
                    AVG(value)::float   AS avg_value,
                    MIN(value)::float   AS min_value,
                    MAX(value)::float   AS max_value,
                    COUNT(*)            AS reading_count,
                    MIN(recorded_at)    AS period_start,
                    MAX(recorded_at)    AS period_end
                FROM iot.sensor_readings
                WHERE device_id = :device_id AND recorded_at >= :since
                GROUP BY device_id, sensor_type
            """),
            {"device_id": device_id, "since": since},
        )
        rows = result.fetchall()
        return [
            DeviceSummaryType(
                device_id=str(r[0]),
                sensor_type=r[1],
                avg_value=r[2],
                min_value=r[3],
                max_value=r[4],
                reading_count=r[5],
                period_start=r[6],
                period_end=r[7],
            )
            for r in rows
        ]


async def resolve_devices(
    info: strawberry.types.Info,
    is_active: Optional[bool] = None,
) -> List[DeviceType]:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        query = "SELECT id, name, device_type, location, is_active, created_at FROM iot.devices"
        params: dict = {}
        if is_active is not None:
            query += " WHERE is_active = :is_active"
            params["is_active"] = is_active
        query += " ORDER BY created_at DESC"
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [
            DeviceType(
                id=str(r[0]),
                name=r[1],
                device_type=r[2],
                location=r[3],
                is_active=r[4],
                created_at=r[5],
            )
            for r in rows
        ]


async def resolve_alerts(
    info: strawberry.types.Info,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[AlertType]:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        query = "SELECT id, rule_id, device_id, triggered_value, severity, status, created_at FROM alerts.alerts"
        conditions, params = [], {}
        if device_id:
            conditions.append("device_id = :device_id")
            params["device_id"] = device_id
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [
            AlertType(
                id=str(r[0]),
                rule_id=str(r[1]),
                device_id=str(r[2]),
                triggered_value=float(r[3]),
                severity=r[4],
                status=r[5],
                created_at=r[6],
            )
            for r in rows
        ]


async def resolve_alert_summary(info: strawberry.types.Info) -> AlertSummaryType:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        result = await session.execute(
            text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'active') AS active,
                    COUNT(*) FILTER (WHERE severity = 'critical') AS critical,
                    COUNT(*) FILTER (WHERE severity = 'warning') AS warning
                FROM alerts.alerts
            """)
        )
        r = result.fetchone()
        return AlertSummaryType(total=r[0], active=r[1], critical=r[2], warning=r[3])
