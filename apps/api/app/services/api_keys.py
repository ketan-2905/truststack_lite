"""Tenant API key lifecycle: creation, authentication, rotation, revocation.

Only the SHA-256 hash and a non-secret prefix are stored. The raw key is
returned exactly once (at creation/rotation) and can never be retrieved again.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.api_key import TenantApiKey
from app.security import generate_api_key, parse_api_key_prefix, verify_api_key


def _now() -> datetime:
    return datetime.now(UTC)


def create_api_key(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    name: str | None = None,
    created_by_user_id: uuid.UUID | None = None,
) -> tuple[TenantApiKey, str]:
    generated = generate_api_key()
    api_key = TenantApiKey(
        tenant_id=tenant_id,
        prefix=generated["prefix"],
        key_hash=generated["key_hash"],
        name=name,
        is_active=True,
        created_by_user_id=created_by_user_id,
    )
    db.add(api_key)
    db.flush()
    return api_key, generated["raw_key"]


def authenticate_api_key(db: Session, raw_key: str) -> TenantApiKey | None:
    prefix = parse_api_key_prefix(raw_key)
    if not prefix:
        return None
    api_key = db.scalar(select(TenantApiKey).where(TenantApiKey.prefix == prefix))
    if api_key is None or not api_key.is_active or api_key.revoked_at is not None:
        return None
    if api_key.expires_at is not None and api_key.expires_at <= _now():
        return None
    if not verify_api_key(raw_key, api_key.key_hash):
        return None
    api_key.last_used_at = _now()
    db.flush()
    return api_key


def list_api_keys(db: Session, tenant_id: uuid.UUID) -> list[TenantApiKey]:
    stmt = (
        select(TenantApiKey)
        .where(TenantApiKey.tenant_id == tenant_id)
        .order_by(TenantApiKey.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def _get_owned_key(db: Session, tenant_id: uuid.UUID, key_id: uuid.UUID) -> TenantApiKey:
    stmt = select(TenantApiKey).where(
        TenantApiKey.id == key_id, TenantApiKey.tenant_id == tenant_id
    )
    api_key = db.scalar(stmt)
    if api_key is None:
        raise NotFoundError("API key")
    return api_key


def revoke_api_key(db: Session, tenant_id: uuid.UUID, key_id: uuid.UUID) -> TenantApiKey:
    api_key = _get_owned_key(db, tenant_id, key_id)
    api_key.is_active = False
    api_key.revoked_at = _now()
    db.flush()
    return api_key


def rotate_api_key(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    expire_old: bool = True,
    created_by_user_id: uuid.UUID | None = None,
) -> tuple[TenantApiKey, str]:
    """Create a new active key. The old key is revoked immediately when
    ``expire_old`` is true; either way the old raw key is never shown again."""
    old = _get_owned_key(db, tenant_id, key_id)
    new_key, raw = create_api_key(
        db, tenant_id=tenant_id, name=old.name, created_by_user_id=created_by_user_id
    )
    if expire_old:
        old.is_active = False
        old.revoked_at = _now()
        db.flush()
    return new_key, raw
