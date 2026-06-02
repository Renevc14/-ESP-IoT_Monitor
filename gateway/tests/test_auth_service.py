"""Unit tests for the gateway authentication service (JWT + bcrypt)."""
import pytest
from jose import JWTError

from app.services.auth_service import (
    _hash_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("S3cret!pass")
    assert hashed != "S3cret!pass"
    assert verify_password("S3cret!pass", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_contains_claims():
    payload = decode_token(create_access_token("user-1", "admin"))
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_refresh_token_type_and_jti():
    payload = decode_token(create_refresh_token("user-1"))
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_decode_tampered_token_raises():
    token = create_access_token("user-1", "viewer")
    with pytest.raises(JWTError):
        decode_token(token + "tampered")


def test_hash_token_is_deterministic_and_distinct():
    assert _hash_token("abc") == _hash_token("abc")
    assert _hash_token("abc") != _hash_token("abd")
