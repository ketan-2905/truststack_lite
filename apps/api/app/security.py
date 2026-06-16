"""Cryptographic primitives: Argon2id password hashing, JWT issuance, and
tenant API-key generation/hashing.

- Passwords are low-entropy → Argon2id.
- API keys are high-entropy random tokens → only the SHA-256 hash is stored
  (GitHub-style ``tsk_<prefix>_<secret>``); the raw key is shown exactly once.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_password_hasher = PasswordHasher()

API_KEY_PREFIX = "tsk"


# ── Passwords ────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(stored_hash)
    except (InvalidHashError, ValueError):
        return False


# ── JWT ──────────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(*, user_id: str, tenant_id: str, roles: list[str]) -> str:
    now = _now()
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: str, tenant_id: str) -> tuple[str, str]:
    now = _now()
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=settings.refresh_token_expire_minutes),
        "jti": jti,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), jti


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jwt.PyJWTError on any problem."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ── API keys ─────────────────────────────────────────────────────────────────
def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), stored_hash)


def generate_api_key() -> dict:
    """Return a new API key: the raw key (show once), its prefix, and its hash."""
    prefix = secrets.token_hex(6)
    secret = secrets.token_urlsafe(32)
    raw_key = f"{API_KEY_PREFIX}_{prefix}_{secret}"
    return {"raw_key": raw_key, "prefix": prefix, "key_hash": hash_api_key(raw_key)}


def parse_api_key_prefix(raw_key: str) -> str | None:
    parts = raw_key.split("_")
    if len(parts) < 3 or parts[0] != API_KEY_PREFIX:
        return None
    return parts[1]
