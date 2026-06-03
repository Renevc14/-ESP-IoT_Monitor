"""Unit tests for the gateway authentication service (JWT + bcrypt + sessions)."""
import uuid
from types import SimpleNamespace

import pytest
from jose import JWTError

from app.services import auth_service as svc


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.added = []
        self.deleted = []

    async def execute(self, *a, **k):
        return FakeResult(self.results.pop(0) if self.results else None)

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        pass


def _user(role="admin"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=SimpleNamespace(value=role),
        is_active=True,
        password_hash=svc.hash_password("S3cret!pass"),
    )


def test_password_hash_roundtrip():
    hashed = svc.hash_password("S3cret!pass")
    assert hashed != "S3cret!pass"
    assert svc.verify_password("S3cret!pass", hashed)
    assert not svc.verify_password("wrong", hashed)


def test_access_token_contains_claims():
    payload = svc.decode_token(svc.create_access_token("user-1", "admin"))
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_refresh_and_reset_token_types():
    assert svc.decode_token(svc.create_refresh_token("u"))["type"] == "refresh"
    assert svc.decode_token(svc.create_reset_token("u"))["type"] == "reset"


def test_decode_tampered_token_raises():
    with pytest.raises(JWTError):
        svc.decode_token(svc.create_access_token("u", "viewer") + "x")


def test_hash_token_deterministic():
    assert svc._hash_token("abc") == svc._hash_token("abc")
    assert svc._hash_token("abc") != svc._hash_token("abd")


@pytest.mark.asyncio
async def test_authenticate_user_ok_and_fail():
    user = _user()
    assert await svc.authenticate_user(FakeSession([user]), "e@e.com", "S3cret!pass") is user
    assert await svc.authenticate_user(FakeSession([user]), "e@e.com", "bad") is None
    assert await svc.authenticate_user(FakeSession([None]), "e@e.com", "x") is None


@pytest.mark.asyncio
async def test_save_refresh_token_adds_session():
    db = FakeSession()
    await svc.save_refresh_token(db, uuid.uuid4(), "tok")
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_rotate_refresh_token_success():
    user = _user()
    token = svc.create_refresh_token(str(user.id))
    session_row = SimpleNamespace(id=1)
    db = FakeSession([session_row, user])  # 1) session lookup 2) user lookup
    result = await svc.rotate_refresh_token(db, token)
    assert result is not None
    rotated_user, access, refresh = result
    assert rotated_user is user
    assert svc.decode_token(access)["type"] == "access"
    assert svc.decode_token(refresh)["type"] == "refresh"
    assert db.deleted  # old session invalidated


@pytest.mark.asyncio
async def test_rotate_refresh_token_invalid():
    assert await svc.rotate_refresh_token(FakeSession(), "not-a-token") is None
    # valid token but no matching session row
    token = svc.create_refresh_token(str(uuid.uuid4()))
    assert await svc.rotate_refresh_token(FakeSession([None]), token) is None


@pytest.mark.asyncio
async def test_rotate_rejects_access_token():
    access = svc.create_access_token("u", "admin")
    assert await svc.rotate_refresh_token(FakeSession([SimpleNamespace()]), access) is None
