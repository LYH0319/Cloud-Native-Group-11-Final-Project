import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import timedelta
from typing import Any

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "group11-dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a password against the stored PBKDF2 hash."""
    if not hashed_password:
        return False
    try:
        scheme, salt, expected = hashed_password.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return hmac.compare_digest(actual, expected)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a compact HS256 JWT access token."""
    ttl = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expires = int(time.time() + ttl.total_seconds())
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = {"sub": subject, "exp": expires}
    if extra_claims:
        payload.update(extra_claims)
    signing_input = ".".join(
        [
            _base64url_encode(
                json.dumps(header, separators=(",", ":")).encode("utf-8")
            ),
            _base64url_encode(
                json.dumps(payload, separators=(",", ":")).encode("utf-8")
            ),
        ]
    )
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a compact HS256 JWT access token."""
    try:
        header_segment, payload_segment, signature = token.split(".", 2)
    except ValueError as error:
        raise ValueError("Invalid token") from error

    signing_input = f"{header_segment}.{payload_segment}"
    if not hmac.compare_digest(_sign(signing_input), signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_base64url_decode(payload_segment))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expired")
    return payload


def _sign(signing_input: str) -> str:
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
