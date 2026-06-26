import pytest

from app.services.auth_service import (
    hash_password, verify_password, create_access_token, decode_access_token
)


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token("owner@example.com")
    subject = decode_access_token(token)
    assert subject == "owner@example.com"


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("not-a-real-token")
