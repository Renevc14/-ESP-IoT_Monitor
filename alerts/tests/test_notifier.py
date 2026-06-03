"""Unit tests for the alert email notifier (best-effort SMTP)."""
import pytest

import app.notifier as notifier


@pytest.mark.asyncio
async def test_noop_without_smtp(monkeypatch):
    monkeypatch.setattr(notifier.settings, "smtp_host", "", raising=False)
    # No recipients / no SMTP → returns without error
    await notifier.send_alert_email([], device_id="d", sensor_type="temperature", value=1, threshold=2, operator="gt", severity="warning")


@pytest.mark.asyncio
async def test_noop_without_recipients(monkeypatch):
    monkeypatch.setattr(notifier.settings, "smtp_host", "mailhog", raising=False)
    sent = {}

    async def fake_send(*a, **k):
        sent["called"] = True

    monkeypatch.setattr(notifier.aiosmtplib, "send", fake_send)
    await notifier.send_alert_email([], device_id="d", sensor_type="t", value=1, threshold=2, operator="gt", severity="warning")
    assert "called" not in sent


@pytest.mark.asyncio
async def test_sends_email(monkeypatch):
    monkeypatch.setattr(notifier.settings, "smtp_host", "mailhog", raising=False)
    captured = {}

    async def fake_send(message, **kwargs):
        captured["to"] = message["To"]
        captured["subject"] = message["Subject"]

    monkeypatch.setattr(notifier.aiosmtplib, "send", fake_send)
    await notifier.send_alert_email(
        ["ops@iot.local"], device_id="dev-1", sensor_type="temperature", value=45.5, threshold=40, operator="gt", severity="critical",
    )
    assert captured["to"] == "ops@iot.local"
    assert "CRITICAL" in captured["subject"]


@pytest.mark.asyncio
async def test_send_swallows_errors(monkeypatch):
    monkeypatch.setattr(notifier.settings, "smtp_host", "mailhog", raising=False)

    async def boom(*a, **k):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notifier.aiosmtplib, "send", boom)
    # Must not raise
    await notifier.send_alert_email(["x@y.z"], device_id="d", sensor_type="t", value=1, threshold=2, operator="gt", severity="warning")
