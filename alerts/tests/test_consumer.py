"""Tests de la política de ack/nack del consumidor (reintento + dead-letter)."""
import pytest

import app.consumer as consumer


class FakeMessage:
    def __init__(self, body=b'{"device_id": "d", "sensor_type": "temperature", "value": 1}', redelivered=False):
        self.body = body
        self.redelivered = redelivered
        self.acked = False
        self.nacked = None  # None = sin nack; True/False = requeue

    async def ack(self):
        self.acked = True

    async def nack(self, requeue=False):
        self.nacked = requeue


@pytest.mark.asyncio
async def test_acks_on_success(monkeypatch):
    async def ok(body, session_factory):
        return None

    monkeypatch.setattr(consumer, "evaluate", ok)
    msg = FakeMessage()
    await consumer.handle_message(msg, lambda: None)
    assert msg.acked is True and msg.nacked is None


@pytest.mark.asyncio
async def test_requeues_on_first_failure(monkeypatch):
    async def boom(body, session_factory):
        raise RuntimeError("transitorio")

    monkeypatch.setattr(consumer, "evaluate", boom)
    msg = FakeMessage(redelivered=False)
    await consumer.handle_message(msg, lambda: None)
    assert msg.acked is False and msg.nacked is True  # reintenta una vez


@pytest.mark.asyncio
async def test_deadletters_on_redelivery(monkeypatch):
    async def boom(body, session_factory):
        raise RuntimeError("veneno")

    monkeypatch.setattr(consumer, "evaluate", boom)
    msg = FakeMessage(redelivered=True)
    await consumer.handle_message(msg, lambda: None)
    assert msg.nacked is False  # sin requeue -> va a la DLQ
