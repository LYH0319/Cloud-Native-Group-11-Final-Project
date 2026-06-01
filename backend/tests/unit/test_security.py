from datetime import timedelta

import pytest

from src.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("secret123")

    assert hashed != "secret123"
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password("secret123", hashed) is True


def test_verify_password_rejects_invalid_passwords_and_hashes():
    hashed = hash_password("secret123")

    assert verify_password("wrong", hashed) is False
    assert verify_password("secret123", None) is False
    assert verify_password("secret123", "not-a-valid-hash") is False
    assert verify_password("secret123", "sha256$salt$digest") is False


def test_access_token_round_trip_decodes_subject():
    token = create_access_token(subject="123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert payload["exp"] > 0


def test_decode_access_token_rejects_expired_token():
    token = create_access_token(
        subject="123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError, match="Token expired"):
        decode_access_token(token)


def test_decode_access_token_rejects_tampered_signature():
    token = create_access_token(subject="123")
    header, payload, _signature = token.split(".", 2)
    tampered_token = f"{header}.{payload}.invalid-signature"

    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(tampered_token)


def test_decode_access_token_rejects_malformed_token():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not-a-jwt")
