"""Unit tests for the analytics export helpers and endpoints."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.routers import export as exp


def test_to_dict_maps_row():
    device_id = uuid.uuid4()
    row = (7, device_id, "temperature", 27.42, "C", datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc))
    result = exp._to_dict(row)
    assert set(result.keys()) == set(exp._COLUMNS)
    assert result["device_id"] == str(device_id)
    assert result["value"] == 27.42


def test_columns_order_is_stable():
    assert exp._COLUMNS == ["id", "device_id", "sensor_type", "value", "unit", "recorded_at"]


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self._rows = rows

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return FakeResult(self._rows)


def _request(rows):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=lambda: FakeSession(rows))))


ROWS = [(1, uuid.uuid4(), "temperature", 27.5, "C", datetime(2026, 1, 1, tzinfo=timezone.utc))]


@pytest.mark.asyncio
async def test_export_csv():
    resp = await exp.export_readings_csv(_request(ROWS), device_id="d", sensor_type="temperature", hours=24, limit=10)
    assert resp.media_type == "text/csv"
    chunks = [c async for c in resp.body_iterator]
    body = "".join(c if isinstance(c, str) else c.decode() for c in chunks)
    assert "temperature" in body and "id,device_id" in body


@pytest.mark.asyncio
async def test_export_json():
    resp = await exp.export_readings_json(_request(ROWS), device_id=None, sensor_type=None, hours=None, limit=10)
    assert resp.status_code == 200
