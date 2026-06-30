"""Tests de validación de payload y autenticación/RBAC de la ingesta."""
import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from pydantic import ValidationError

import app.routers.ingest as ingest
from app.config import settings
from app.schemas.reading import ReadingPayload


def _token(role="operator", token_type="access"):
    return jwt.encode({"sub": "u1", "role": role, "type": token_type}, settings.jwt_secret_key, algorithm="HS256")


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_verify_jwt_valid():
    payload = ingest.verify_jwt(_creds(_token()))
    assert payload["role"] == "operator"


def test_verify_jwt_invalid():
    with pytest.raises(HTTPException) as exc:
        ingest.verify_jwt(_creds("not-a-jwt"))
    assert exc.value.status_code == 401


def test_verify_jwt_rejects_refresh():
    with pytest.raises(HTTPException):
        ingest.verify_jwt(_creds(_token(token_type="refresh")))


def test_payload_rejects_unknown_sensor():
    with pytest.raises(ValidationError):
        ReadingPayload(device_id=uuid.uuid4(), sensor_type="presion", value=1.0, unit="bar")


def test_payload_rejects_non_finite_value():
    with pytest.raises(ValidationError):
        ReadingPayload(device_id=uuid.uuid4(), sensor_type="temperature", value=float("nan"), unit="C")


@pytest.mark.asyncio
async def test_ingest_blocks_viewer():
    body = ReadingPayload(device_id=uuid.uuid4(), sensor_type="temperature", value=20.0, unit="C")
    with pytest.raises(HTTPException) as exc:
        await ingest.ingest_reading(body, token_payload={"role": "viewer", "sub": "u1"})
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_ingest_operator_publishes(monkeypatch):
    published = {}

    async def fake_publish(message):
        published["msg"] = message

    monkeypatch.setattr(ingest.publisher, "publish", fake_publish)
    body = ReadingPayload(device_id=uuid.uuid4(), sensor_type="temperature", value=20.0, unit="C")
    resp = await ingest.ingest_reading(body, token_payload={"role": "operator", "sub": "u1"})
    assert resp.published is True
    assert published["msg"]["sensor_type"] == "temperature"
