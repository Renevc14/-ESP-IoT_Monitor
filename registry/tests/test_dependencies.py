"""Tests de la autenticación por claims del registry (RBAC)."""
import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

import app.dependencies as deps
from app.config import settings


def _token(role="admin", token_type="access"):
    payload = {"sub": str(uuid.uuid4()), "role": role, "type": token_type}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_principal_valid_token():
    p = deps.get_current_principal(_creds(_token("operator")))
    assert p.role == "operator" and p.id is not None


def test_principal_rejects_garbage():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_principal(_creds("not-a-jwt"))
    assert exc.value.status_code == 401


def test_principal_rejects_refresh():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_principal(_creds(_token(token_type="refresh")))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_operator_allows_operator():
    p = deps.Principal("u1", "operator")
    assert await deps.require_operator(p) is p


@pytest.mark.asyncio
async def test_require_admin_blocks_operator():
    with pytest.raises(HTTPException) as exc:
        await deps.require_admin(deps.Principal("u1", "operator"))
    assert exc.value.status_code == 403
