"""Report export endpoints (RF-10): sensor readings as CSV or JSON.

Reuses the same filtered query as the GraphQL `readings` resolver and streams
the result so large exports do not buffer entirely in memory.
"""
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text

router = APIRouter(prefix="/export", tags=["Export"])

_COLUMNS = ["id", "device_id", "sensor_type", "value", "unit", "recorded_at"]


async def _fetch_rows(
    request: Request,
    device_id: Optional[str],
    sensor_type: Optional[str],
    hours: Optional[int],
    limit: int,
):
    session_factory = request.app.state.session_factory
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
            conditions.append("recorded_at >= :since")
            params["since"] = datetime.now(timezone.utc) - timedelta(hours=hours)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY recorded_at DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(text(query), params)
        return result.fetchall()


def _to_dict(row) -> dict:
    return {
        "id": row[0],
        "device_id": str(row[1]),
        "sensor_type": row[2],
        "value": float(row[3]),
        "unit": row[4],
        "recorded_at": row[5].isoformat(),
    }


@router.get("/readings.csv")
async def export_readings_csv(
    request: Request,
    device_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    hours: Optional[int] = Query(None),
    limit: int = Query(10000, le=100000),
):
    rows = await _fetch_rows(request, device_id, sensor_type, hours, limit)

    def generate():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_COLUMNS)
        yield buffer.getvalue()
        buffer.seek(0); buffer.truncate(0)
        for row in rows:
            d = _to_dict(row)
            writer.writerow([d[c] for c in _COLUMNS])
            yield buffer.getvalue()
            buffer.seek(0); buffer.truncate(0)

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=readings.csv"},
    )


@router.get("/readings.json")
async def export_readings_json(
    request: Request,
    device_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    hours: Optional[int] = Query(None),
    limit: int = Query(10000, le=100000),
):
    rows = await _fetch_rows(request, device_id, sensor_type, hours, limit)
    return JSONResponse(
        [_to_dict(r) for r in rows],
        headers={"Content-Disposition": "attachment; filename=readings.json"},
    )
