"""Unit tests for alert evaluation (operators + full evaluate path)."""
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


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeSession:
    def __init__(self, rules):
        self.rules = rules
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return FakeResult(self.rules)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


def _rule(operator="gt", threshold=40.0, severity="critical", emails=None):
    return type("Rule", (), {
        "id": uuid.uuid4(),
        "device_id": uuid.uuid4(),
        "operator": operator,
        "threshold": threshold,
        "severity": severity,
        "notification_emails": emails or [],
    })()


def _factory(rules):
    return lambda: FakeSession(rules)


def _patch(monkeypatch):
    broadcasts, emails = [], []

    async def fake_broadcast(payload):
        broadcasts.append(payload)

    async def fake_email(recipients, **kwargs):
        emails.append((recipients, kwargs))

    monkeypatch.setattr(ev.manager, "broadcast", fake_broadcast)
    monkeypatch.setattr(ev, "send_alert_email", fake_email)
    return broadcasts, emails


@pytest.mark.asyncio
async def test_evaluate_triggers_alert(monkeypatch):
    rule = _rule(operator="gt", threshold=40.0, severity="critical", emails=["ops@iot.local"])
    broadcasts, emails = _patch(monkeypatch)
    await ev.evaluate(
        {"device_id": str(rule.device_id), "sensor_type": "temperature", "value": 45.5},
        _factory([rule]),
    )
    assert len(broadcasts) == 1
    assert broadcasts[0]["severity"] == "critical"
    assert broadcasts[0]["event"] == "alert_triggered"
    assert emails and emails[0][0] == ["ops@iot.local"]


@pytest.mark.asyncio
async def test_evaluate_no_alert_below_threshold(monkeypatch):
    rule = _rule(operator="gt", threshold=40.0)
    broadcasts, emails = _patch(monkeypatch)
    await ev.evaluate(
        {"device_id": str(rule.device_id), "sensor_type": "temperature", "value": 21.0},
        _factory([rule]),
    )
    assert broadcasts == []
    assert emails == []
