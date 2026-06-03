"""Tests de la autenticación basada en claims del JWT."""
import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

import app.dependencies as deps
from app.config import settings


def _token(role="admin", token_type="access"):
    payload = {"sub": str(uuid.uuid4()), "role": role, "type": token_type}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_principal_valid_token():
    principal = deps.get_current_principal(_creds(_token("admin")))
    assert principal.role == "admin" and principal.id is not None


def test_principal_rejects_garbage():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_principal(_creds("not-a-jwt"))
    assert exc.value.status_code == 401


def test_principal_rejects_refresh_token():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_principal(_creds(_token(token_type="refresh")))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_role_allows_matching_role():
    check = deps.require_role("admin", "operator")
    principal = deps.Principal("u1", "operator")
    assert await check(principal) is principal


@pytest.mark.asyncio
async def test_require_role_blocks_other_role():
    check = deps.require_role("admin")
    with pytest.raises(HTTPException) as exc:
        await check(deps.Principal("u1", "viewer"))
    assert exc.value.status_code == 403
