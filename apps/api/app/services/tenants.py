"""Tenant repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def get_tenant(db: Session, tenant_id: uuid.UUID) -> Tenant | None:
    return db.get(Tenant, tenant_id)


def get_active_tenant(db: Session, tenant_id: uuid.UUID) -> Tenant | None:
    stmt = select(Tenant).where(
        Tenant.id == tenant_id,
        Tenant.deleted_at.is_(None),
        Tenant.status == "active",
    )
    return db.scalar(stmt)


def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.deleted_at.is_(None))
    return db.scalar(stmt)
