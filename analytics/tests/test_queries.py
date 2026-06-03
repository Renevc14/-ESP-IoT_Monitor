"""Unit tests for GraphQL query resolvers (with a fake DB session)."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.resolvers import queries


class FakeResult:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._one


class FakeSession:
    def __init__(self, result):
        self._result = result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return self._result


def _info(result):
    return SimpleNamespace(context={"session_factory": lambda: FakeSession(result)})


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_resolve_readings():
    rows = [(1, "dev", "temperature", 27.5, "C", NOW)]
    out = await queries.resolve_readings(_info(FakeResult(rows)), device_id="dev", sensor_type="temperature", hours=24)
    assert out[0].value == 27.5 and out[0].sensor_type == "temperature"


@pytest.mark.asyncio
async def test_resolve_device_summary():
    rows = [("dev", "temperature", 20.0, 10.0, 30.0, 28.0, 5.0, 12, NOW, NOW)]
    out = await queries.resolve_device_summary(_info(FakeResult(rows)), device_id="dev", hours=24)
    assert out[0].p95_value == 28.0 and out[0].trend == 5.0


@pytest.mark.asyncio
async def test_resolve_devices():
    rows = [("id1", "Sensor", "multi_sensor", "Lab", True, NOW)]
    out = await queries.resolve_devices(_info(FakeResult(rows)), is_active=True)
    assert out[0].name == "Sensor"


@pytest.mark.asyncio
async def test_resolve_alerts():
    rows = [("a1", "r1", "d1", 45.5, "critical", "active", NOW)]
    out = await queries.resolve_alerts(_info(FakeResult(rows)), device_id="d1", status="active")
    assert out[0].severity == "critical"


@pytest.mark.asyncio
async def test_resolve_alert_summary():
    out = await queries.resolve_alert_summary(_info(FakeResult(one=(10, 4, 2, 2))))
    assert out.total == 10 and out.active == 4


@pytest.mark.asyncio
async def test_resolve_bucketed_readings():
    rows = [(NOW, 20.0, 10.0, 30.0, 6)]
    out = await queries.resolve_bucketed_readings(_info(FakeResult(rows)), device_id="d", sensor_type="temperature", hours=24, bucket_minutes=30)
    assert out[0].avg_value == 20.0 and out[0].reading_count == 6
