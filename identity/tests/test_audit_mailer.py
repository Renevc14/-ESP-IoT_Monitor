"""Unit tests for audit logging and the SMTP mailer (best-effort)."""
import uuid
from types import SimpleNamespace

import pytest

import app.services.audit_service as audit
import app.services.mailer as mailer


def test_client_ip():
    assert audit.client_ip(None) is None
    assert audit.client_ip(SimpleNamespace(client=None)) is None
    assert audit.client_ip(SimpleNamespace(client=SimpleNamespace(host="9.9.9.9"))) == "9.9.9.9"


class FakeCtxSession:
    def __init__(self):
        self.executed = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        self.executed.append((a, k))

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_log_event_writes(monkeypatch):
    session = FakeCtxSession()
    monkeypatch.setattr(audit, "AsyncSessionLocal", lambda: session)
    await audit.log_event("login_success", user_id=uuid.uuid4(), resource="/x", ip="1.2.3.4", details={"a": 1})
    assert session.executed and session.committed


@pytest.mark.asyncio
async def test_log_event_swallows_errors(monkeypatch):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(audit, "AsyncSessionLocal", boom)
    # Must not raise
    await audit.log_event("x")


@pytest.mark.asyncio
async def test_mailer_noop_without_smtp(monkeypatch):
    monkeypatch.setattr(mailer.settings, "smtp_host", "", raising=False)
    await mailer.send_email("to@x.com", "s", "b")  # no raise, no send


@pytest.mark.asyncio
async def test_mailer_sends_when_configured(monkeypatch):
    sent = {}

    async def fake_send(message, **kwargs):
        sent["to"] = message["To"]
        sent["kwargs"] = kwargs

    monkeypatch.setattr(mailer.settings, "smtp_host", "mailhog", raising=False)
    monkeypatch.setattr(mailer.aiosmtplib, "send", fake_send)
    await mailer.send_email("to@x.com", "Asunto", "Cuerpo")
    assert sent["to"] == "to@x.com"
