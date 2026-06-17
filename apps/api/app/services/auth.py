"""User authentication and refresh-token lifecycle (Redis allowlist)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import RoleName
from app.models.role import Role, UserRole
from app.models.user import User
from app.redis_client import get_redis
from app.security import verify_password
from app.services import tenants as tenant_service

REFRESH_KEY_PREFIX = "refresh"


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
    tenant_slug: str | None = None,
) -> User | None:
    stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
    if tenant_slug:
        tenant = tenant_service.get_tenant_by_slug(db, tenant_slug)
        if tenant is None:
            return None
        stmt = stmt.where(User.tenant_id == tenant.id)

    users = db.scalars(stmt).all()
    # Email is unique per tenant; if it resolves to multiple tenants, require a
    # tenant_slug to disambiguate rather than guess.
    if len(users) != 1:
        return None
    user = users[0]
    if not user.is_active or not verify_password(user.hashed_password, password):
        return None
    return user


def get_user_role_names(db: Session, user: User) -> list[str]:
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    return [r.value if isinstance(r, RoleName) else str(r) for r in db.scalars(stmt).all()]


# ── Refresh token allowlist (revocable via Redis) ────────────────────────────
def store_refresh_jti(jti: str, user_id: uuid.UUID, ttl_seconds: int) -> None:
    get_redis().set(f"{REFRESH_KEY_PREFIX}:{jti}", str(user_id), ex=ttl_seconds)


def is_refresh_active(jti: str) -> bool:
    return get_redis().exists(f"{REFRESH_KEY_PREFIX}:{jti}") == 1


def revoke_refresh_jti(jti: str) -> None:
    get_redis().delete(f"{REFRESH_KEY_PREFIX}:{jti}")
