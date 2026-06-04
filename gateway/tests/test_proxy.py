"""Unit tests del proxy de borde: enrutamiento por prefijo y validación de token."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from jose import jwt

import app.proxy as proxy
from app.config import settings


def test_upstream_routing():
    assert proxy._upstream_for("/auth/login") == settings.identity_url
    assert proxy._upstream_for("/users") == settings.identity_url
    assert proxy._upstream_for("/devices") == settings.registry_url
    assert proxy._upstream_for("/devices/123") == settings.registry_url
    assert proxy._upstream_for("/alert-rules") == settings.alerts_url
    assert proxy._upstream_for("/alerts/abc/resolve") == settings.alerts_url
    assert proxy._upstream_for("/desconocido") is None


def _request(auth: str | None):
    headers = {"authorization": auth} if auth else {}
    return SimpleNamespace(headers=headers)


def _token(token_type="access"):
    return jwt.encode({"sub": "u1", "type": token_type}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def test_valid_token_passes():
    proxy._require_valid_token(_request(f"Bearer {_token()}"))  # no raise


def test_missing_token_rejected():
    with pytest.raises(HTTPException) as exc:
        proxy._require_valid_token(_request(None))
    assert exc.value.status_code == 401


def test_refresh_token_rejected():
    with pytest.raises(HTTPException) as exc:
        proxy._require_valid_token(_request(f"Bearer {_token('refresh')}"))
    assert exc.value.status_code == 401
