"""Unit tests for GraphQL query resolvers.

readings/deviceSummary/bucketedReadings leen timeseries-db (sesión simulada);
devices/alerts/alertSummary se componen por HTTP (cliente httpx simulado).
"""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.resolvers import queries


# ── Fakes para la BD de series ──────────────────────────────────────────────
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


# ── Fakes para el cliente HTTP compartido (composición de API) ──────────────
class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, data):
        self._data = data

    async def get(self, *a, **k):
        return FakeResp(self._data)


def _info(result=None, http=None):
    return SimpleNamespace(
        context={"session_factory": lambda: FakeSession(result), "auth": None, "http": http}
    )


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
ISO = "2026-01-01T12:00:00+00:00"


@pytest.mark.asyncio
async def test_resolve_readings():
    rows = [(1, "dev", "temperature", 27.5, "C", NOW)]
    out = await queries.resolve_readings(_info(FakeResult(rows)), device_id="dev", sensor_type="temperature", hours=24)
    assert out[0].value == 27.5


@pytest.mark.asyncio
async def test_resolve_device_summary():
    rows = [("dev", "temperature", 20.0, 10.0, 30.0, 28.0, 5.0, 12, NOW, NOW)]
    out = await queries.resolve_device_summary(_info(FakeResult(rows)), device_id="dev", hours=24)
    assert out[0].p95_value == 28.0 and out[0].trend == 5.0


@pytest.mark.asyncio
async def test_resolve_bucketed_readings():
    rows = [(NOW, 20.0, 10.0, 30.0, 6)]
    out = await queries.resolve_bucketed_readings(_info(FakeResult(rows)), device_id="d", sensor_type="temperature", hours=24, bucket_minutes=30)
    assert out[0].avg_value == 20.0


@pytest.mark.asyncio
async def test_resolve_hourly_readings():
    rows = [(NOW, 21.5, 18.0, 25.0, 60)]
    out = await queries.resolve_hourly_readings(_info(FakeResult(rows)), device_id="d", sensor_type="temperature", days=7)
    assert out[0].avg_value == 21.5 and out[0].reading_count == 60


@pytest.mark.asyncio
async def test_resolve_devices_composition():
    http = FakeClient([{"id": "d1", "name": "Sensor", "device_type": "multi_sensor", "location": "Lab", "is_active": True, "created_at": ISO}])
    out = await queries.resolve_devices(_info(http=http), is_active=True)
    assert out[0].name == "Sensor" and out[0].device_type == "multi_sensor"


@pytest.mark.asyncio
async def test_resolve_alerts_composition():
    http = FakeClient([{"id": "a1", "device_id": "d1", "triggered_value": 45.5, "severity": "critical", "status": "active", "created_at": ISO}])
    out = await queries.resolve_alerts(_info(http=http), device_id="d1", status="active")
    assert out[0].severity == "critical"


@pytest.mark.asyncio
async def test_resolve_alert_summary_composition():
    http = FakeClient({"total": 5, "active": 2, "critical": 1, "warning": 1})
    out = await queries.resolve_alert_summary(_info(http=http))
    assert out.total == 5 and out.active == 2
