"""Unit tests for the alert evaluation logic (threshold operators + evaluate)."""
import uuid

import pytest

import app.evaluator as ev


def test_operator_truth_table():
    assert ev._OPERATORS["gt"](45, 40)
    assert not ev._OPERATORS["gt"](40, 40)
    assert ev._OPERATORS["lt"](5, 10)
    assert not ev._OPERATORS["lt"](10, 10)
    assert ev._OPERATORS["gte"](40, 40)
    assert ev._OPERATORS["lte"](40, 40)
    assert not ev._OPERATORS["lte"](41, 40)


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


def _fake_factory():
    return _FakeSession()


def _rule(operator="gt", threshold=40.0, severity="critical", emails=None):
    return type("Rule", (), {
        "id": uuid.uuid4(),
        "device_id": uuid.uuid4(),
        "operator": operator,
        "threshold": threshold,
        "severity": severity,
        "notification_emails": emails or [],
    })()


def _patch_common(monkeypatch, rules):
    broadcasts, emails = [], []

    async def fake_rules(session, device_id, sensor_type):
        return rules

    async def fake_create(session, rule, value):
        return type("Alert", (), {"id": uuid.uuid4(), "device_id": rule.device_id, "severity": rule.severity})()

    async def fake_broadcast(payload):
        broadcasts.append(payload)

    async def fake_email(recipients, **kwargs):
        emails.append((recipients, kwargs))

    monkeypatch.setattr(ev, "_get_active_rules", fake_rules)
    monkeypatch.setattr(ev, "_create_alert", fake_create)
    monkeypatch.setattr(ev.manager, "broadcast", fake_broadcast)
    monkeypatch.setattr(ev, "send_alert_email", fake_email)
    return broadcasts, emails


@pytest.mark.asyncio
async def test_evaluate_triggers_alert_above_threshold(monkeypatch):
    rule = _rule(operator="gt", threshold=40.0, severity="critical")
    broadcasts, emails = _patch_common(monkeypatch, [rule])

    await ev.evaluate(
        {"device_id": str(rule.device_id), "sensor_type": "temperature", "value": 45.5},
        _fake_factory,
    )

    assert len(broadcasts) == 1
    assert broadcasts[0]["severity"] == "critical"
    assert broadcasts[0]["event"] == "alert_triggered"
    assert len(emails) == 1


@pytest.mark.asyncio
async def test_evaluate_no_alert_below_threshold(monkeypatch):
    rule = _rule(operator="gt", threshold=40.0)
    broadcasts, emails = _patch_common(monkeypatch, [rule])

    await ev.evaluate(
        {"device_id": str(rule.device_id), "sensor_type": "temperature", "value": 21.0},
        _fake_factory,
    )

    assert broadcasts == []
    assert emails == []
