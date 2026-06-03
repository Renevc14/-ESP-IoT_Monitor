"""Unit tests for auth dependencies (current user + RBAC)."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import app.dependencies as deps
from app.models.user import UserRole
from app.services.auth_service import create_access_token, create_refresh_token


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    def __init__(self, value):
        self._value = value

    async def execute(self, *a, **k):
        return FakeResult(self._value)


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_get_current_user_ok():
    user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.admin, is_active=True)
    token = create_access_token(str(user.id), "admin")
    result = await deps.get_current_user(_creds(token), FakeSession(user))
    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user(_creds("bad-token"), FakeSession(None))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_refresh_token():
    token = create_refresh_token(str(uuid.uuid4()))
    with pytest.raises(HTTPException):
        await deps.get_current_user(_creds(token), FakeSession(None))


@pytest.mark.asyncio
async def test_require_role_allows(monkeypatch):
    user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.admin)
    check = deps.require_role(UserRole.admin)
    assert await check(SimpleNamespace(), user) is user


@pytest.mark.asyncio
async def test_require_role_denies(monkeypatch):
    logged = {}

    async def fake_log(action, **kw):
        logged["action"] = action

    monkeypatch.setattr(deps, "log_event", fake_log)
    request = SimpleNamespace(
        method="POST",
        url=SimpleNamespace(path="/users"),
        client=SimpleNamespace(host="1.2.3.4"),
    )
    user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.viewer)
    check = deps.require_role(UserRole.admin)
    with pytest.raises(HTTPException) as exc:
        await check(request, user)
    assert exc.value.status_code == 403
    assert logged["action"] == "access_denied"
