"""Idempotency-key storage for external client requests."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyKey


def get(db: Session, tenant_id: uuid.UUID, key: str) -> IdempotencyKey | None:
    return db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == tenant_id, IdempotencyKey.key == key
        )
    )


def store(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    key: str,
    resource_type: str,
    resource_id: str,
    response_code: int,
    response_body: dict,
) -> IdempotencyKey:
    record = IdempotencyKey(
        tenant_id=tenant_id,
        key=key,
        resource_type=resource_type,
        resource_id=resource_id,
        response_code=response_code,
        response_body=response_body,
    )
    db.add(record)
    db.flush()
    return record
