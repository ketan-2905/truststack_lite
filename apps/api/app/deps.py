"""Request-scoped dependencies: request context, the authenticated principal,
and role-based authorization.

The tenant is resolved from credentials only — an ``X-API-Key`` header for B2B
tenant clients, or a ``Authorization: Bearer <jwt>`` access token for dashboard
users. There is no client-supplied tenant header, so cross-tenant access is not
possible by spoofing a header.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import RoleName
from app.errors import ForbiddenError, UnauthorizedError
from app.models.tenant import Tenant
from app.security import decode_token
from app.services import api_keys as api_key_service
from app.services import audit
from app.services import tenants as tenant_service

# API-key principals act with this implicit role (machine/tenant client).
API_KEY_ROLES: set[RoleName] = {RoleName.system}
# Convenience role groups for authorization.
ALL_TENANT_ROLES: set[RoleName] = {
    RoleName.tenant_admin,
    RoleName.analyst,
    RoleName.viewer,
    RoleName.system,
}
WRITE_ROLES: set[RoleName] = {RoleName.tenant_admin, RoleName.system}


@dataclass
class RequestContext:
    request_id: str | None
    ip: str | None
    user_agent: str | None


@dataclass
class Principal:
    tenant: Tenant
    actor_type: str  # "api_key" | "user"
    actor_id: str | None
    roles: set[RoleName] = field(default_factory=set)
    request: RequestContext | None = None

    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id


def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        request_id=getattr(request.state, "request_id", None),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _principal_from_api_key(db: Session, raw_key: str, ctx: RequestContext) -> Principal:
    api_key = api_key_service.authenticate_api_key(db, raw_key)
    if api_key is None:
        raise UnauthorizedError("Invalid or expired API key.")
    tenant = tenant_service.get_active_tenant(db, api_key.tenant_id)
    if tenant is None:
        raise UnauthorizedError("Tenant is inactive.")
    return Principal(
        tenant=tenant,
        actor_type="api_key",
        actor_id=str(api_key.id),
        roles=set(API_KEY_ROLES),
        request=ctx,
    )


def _principal_from_jwt(db: Session, token: str, ctx: RequestContext) -> Principal:
    try:
        claims = decode_token(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if claims.get("type") != "access":
        raise UnauthorizedError("An access token is required.")

    try:
        tenant_id = uuid.UUID(claims["tenant_id"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token.") from exc

    tenant = tenant_service.get_active_tenant(db, tenant_id)
    if tenant is None:
        raise UnauthorizedError("Tenant is inactive.")

    roles: set[RoleName] = set()
    for role in claims.get("roles", []):
        try:
            roles.add(RoleName(role))
        except ValueError:
            continue
    return Principal(
        tenant=tenant,
        actor_type="user",
        actor_id=claims.get("sub"),
        roles=roles,
        request=ctx,
    )


def get_principal(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Principal:
    ctx = get_request_context(request)

    if x_api_key:
        return _principal_from_api_key(db, x_api_key, ctx)

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        return _principal_from_jwt(db, token, ctx)

    raise UnauthorizedError(
        "Authentication required: provide X-API-Key or a Bearer access token."
    )


def require_roles(*allowed: RoleName) -> Callable[..., Principal]:
    """Dependency factory enforcing that the principal holds one of ``allowed``.

    Forbidden attempts are audited in an independent transaction so the event is
    persisted even though the request fails.
    """
    allowed_set = set(allowed)

    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not (principal.roles & allowed_set):
            audit.record_event_committed(
                tenant_id=principal.tenant_id,
                actor_type=principal.actor_type,
                actor_id=principal.actor_id,
                action="access.forbidden",
                resource_type="authorization",
                request=principal.request,
                data={
                    "required": [r.value for r in allowed_set],
                    "held": [r.value for r in principal.roles],
                },
            )
            raise ForbiddenError("You do not have the required role for this action.")
        return principal

    return _dependency
