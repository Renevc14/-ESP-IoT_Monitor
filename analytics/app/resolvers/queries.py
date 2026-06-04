from datetime import datetime, timedelta, timezone
from typing import List, Optional

import strawberry
from sqlalchemy import text

from app.config import settings

from app.types.schema import AlertSummaryType, AlertType, BucketedReadingType, DeviceSummaryType, DeviceType, SensorReadingType

# Tope defensivo para el argumento `limit` (evita escaneos/serializaciones abusivas).
MAX_LIMIT = 1000


async def resolve_readings(
    info: strawberry.types.Info,
    device_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    limit: int = 100,
    hours: Optional[int] = None,
) -> List[SensorReadingType]:
    limit = max(1, min(limit, MAX_LIMIT))
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
        if hours is not None:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            conditions.append("recorded_at >= :since")
            params["since"] = since

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
                    AVG(value)::float                                           AS avg_value,
                    MIN(value)::float                                           AS min_value,
                    MAX(value)::float                                           AS max_value,
                    percentile_cont(0.95) WITHIN GROUP (ORDER BY value)::float  AS p95_value,
                    (last(value, recorded_at) - first(value, recorded_at))::float AS trend,
                    COUNT(*)                                                    AS reading_count,
                    MIN(recorded_at)                                            AS period_start,
                    MAX(recorded_at)                                            AS period_end
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
                p95_value=r[5],
                trend=r[6],
                reading_count=r[7],
                period_start=r[8],
                period_end=r[9],
            )
            for r in rows
        ]


# ── Composición de API (datos de otros servicios) ───────────────────────────
# devices vive en registry, alerts en el servicio de alertas. Analytics (lado de
# lectura/CQRS) los compone vía HTTP en lugar de hacer JOIN entre bases.

def _auth_headers(info) -> dict:
    auth = info.context.get("auth")
    return {"Authorization": auth} if auth else {}


async def resolve_devices(
    info: strawberry.types.Info,
    is_active: Optional[bool] = None,
) -> List[DeviceType]:
    client = info.context["http"]
    resp = await client.get(f"{settings.registry_url}/devices", headers=_auth_headers(info))
    resp.raise_for_status()
    rows = resp.json()
    return [
        DeviceType(
            id=str(d["id"]),
            name=d["name"],
            device_type=d["device_type"],
            location=d.get("location"),
            is_active=d["is_active"],
            created_at=datetime.fromisoformat(d["created_at"]),
        )
        for d in rows
        if is_active is None or d["is_active"] == is_active
    ]


async def resolve_alerts(
    info: strawberry.types.Info,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[AlertType]:
    limit = max(1, min(limit, MAX_LIMIT))
    params: dict = {"limit": limit}
    if status:
        params["status"] = status
    client = info.context["http"]
    resp = await client.get(f"{settings.alerts_url}/alerts", params=params, headers=_auth_headers(info))
    resp.raise_for_status()
    rows = resp.json()
    out = []
    for a in rows:
        if device_id and str(a["device_id"]) != device_id:
            continue
        out.append(AlertType(
            id=str(a["id"]),
            rule_id="",
            device_id=str(a["device_id"]),
            triggered_value=float(a["triggered_value"]),
            severity=a["severity"],
            status=a["status"],
            created_at=datetime.fromisoformat(a["created_at"]),
        ))
    return out


async def resolve_alert_summary(info: strawberry.types.Info) -> AlertSummaryType:
    client = info.context["http"]
    resp = await client.get(f"{settings.alerts_url}/alerts/summary", headers=_auth_headers(info))
    resp.raise_for_status()
    d = resp.json()
    return AlertSummaryType(total=d["total"], active=d["active"], critical=d["critical"], warning=d["warning"])


async def resolve_hourly_readings(
    info: strawberry.types.Info,
    device_id: str,
    sensor_type: str,
    days: int = 7,
) -> List[BucketedReadingType]:
    """Tendencias horarias leídas del continuous aggregate de TimescaleDB.

    A diferencia de bucketed_readings (recalcula time_bucket sobre la tabla cruda),
    esto consulta la vista materializada incremental: O(filas del periodo agregado).
    """
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await session.execute(
            text("""
                SELECT bucket, avg_value::float, min_value::float, max_value::float, reading_count
                FROM iot.sensor_readings_hourly
                WHERE device_id = :device_id
                  AND sensor_type = :sensor_type
                  AND bucket >= :since
                ORDER BY bucket ASC
            """),
            {"device_id": device_id, "sensor_type": sensor_type, "since": since},
        )
        return [
            BucketedReadingType(
                bucket=r[0], avg_value=r[1], min_value=r[2], max_value=r[3], reading_count=r[4]
            )
            for r in result.fetchall()
        ]


async def resolve_bucketed_readings(
    info: strawberry.types.Info,
    device_id: str,
    sensor_type: str,
    hours: int = 24,
    bucket_minutes: int = 30,
) -> List[BucketedReadingType]:
    session_factory = info.context["session_factory"]
    async with session_factory() as session:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await session.execute(
            text("""
                SELECT
                    time_bucket(:bucket_interval, recorded_at) AS bucket,
                    AVG(value)::float   AS avg_value,
                    MIN(value)::float   AS min_value,
                    MAX(value)::float   AS max_value,
                    COUNT(*)            AS reading_count
                FROM iot.sensor_readings
                WHERE device_id = :device_id
                  AND sensor_type = :sensor_type
                  AND recorded_at >= :since
                GROUP BY bucket
                ORDER BY bucket ASC
            """),
            {
                "bucket_interval": timedelta(minutes=bucket_minutes),
                "device_id": device_id,
                "sensor_type": sensor_type,
                "since": since,
            },
        )
        rows = result.fetchall()
        return [
            BucketedReadingType(
                bucket=r[0],
                avg_value=r[1],
                min_value=r[2],
                max_value=r[3],
                reading_count=r[4],
            )
            for r in rows
        ]
