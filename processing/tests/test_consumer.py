"""Tests de handle_message: idempotencia, ack/poison/transitorio."""
import json

import pytest

import app.consumer as consumer
from app.consumer import _IncomingReading

VALID = json.dumps({
    "device_id": "d0000000-0000-0000-0000-000000000001",
    "sensor_type": "temperature",
    "value": 21.5,
    "unit": "C",
    "recorded_at": "2030-01-01T00:00:00+00:00",
}).encode()


class FakeMessage:
    def __init__(self, body, redelivered=False):
        self.body = body
        self.redelivered = redelivered
        self.acked = False
        self.nacked = None

    async def ack(self):
        self.acked = True

    async def nack(self, requeue=False):
        self.nacked = requeue


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return None

    async def commit(self):
        pass


class FakeRedis:
    async def setex(self, *a, **k):
        pass


@pytest.mark.asyncio
async def test_persist_and_cache_runs():
    reading = _IncomingReading.model_validate(json.loads(VALID))
    await consumer._persist_and_cache(reading, lambda: FakeSession(), FakeRedis())


@pytest.mark.asyncio
async def test_handle_acks_on_success():
    msg = FakeMessage(VALID)
    await consumer.handle_message(msg, lambda: FakeSession(), FakeRedis())
    assert msg.acked is True and msg.nacked is None


@pytest.mark.asyncio
async def test_handle_poison_invalid_json():
    msg = FakeMessage(b"no-es-json")
    await consumer.handle_message(msg, lambda: FakeSession(), FakeRedis())
    assert msg.nacked is False and msg.acked is False


@pytest.mark.asyncio
async def test_handle_poison_non_finite_value():
    bad = json.dumps({
        "device_id": "d0000000-0000-0000-0000-000000000001",
        "sensor_type": "temperature", "value": float("inf"),
        "unit": "C", "recorded_at": "2030-01-01T00:00:00+00:00",
    }).encode()
    msg = FakeMessage(bad)
    await consumer.handle_message(msg, lambda: FakeSession(), FakeRedis())
    assert msg.nacked is False


@pytest.mark.asyncio
async def test_handle_transient_retries_then_dlq(monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("BD caída")

    monkeypatch.setattr(consumer, "_persist_and_cache", boom)
    first = FakeMessage(VALID, redelivered=False)
    await consumer.handle_message(first, lambda: FakeSession(), FakeRedis())
    assert first.nacked is True  # reintenta una vez

    second = FakeMessage(VALID, redelivered=True)
    await consumer.handle_message(second, lambda: FakeSession(), FakeRedis())
    assert second.nacked is False  # luego a la DLQ
