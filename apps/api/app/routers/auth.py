"""Authentication endpoints for dashboard users (JWT)."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_request_context
from app.errors import UnauthorizedError
from app.rate_limit import enforce_rate_limit
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.security import create_access_token, create_refresh_token, decode_token
from app.services import audit
from app.services import auth as auth_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    ctx = get_request_context(request)
    ip = ctx.ip or "unknown"

    # Throttle brute-force attempts before doing any expensive password hashing.
    enforce_rate_limit(
        key=f"auth:login:{ip}:{payload.email}",
        limit=settings.rate_limit_auth_per_minute,
    )

    user = auth_service.authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
        tenant_slug=payload.tenant_slug,
    )
    if user is None:
        audit.record_event_committed(
            action="auth.login_failed",
            resource_type="user",
            actor_type="user",
            actor_id=payload.email,
            request=ctx,
            data={"email": payload.email},
        )
        raise UnauthorizedError("Invalid email or password.")

    roles = auth_service.get_user_role_names(db, user)
    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, roles=roles)
    refresh, jti = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id)
    auth_service.store_refresh_jti(
        jti, user.id, settings.refresh_token_expire_minutes * 60
    )

    audit.record_event(
        db,
        tenant_id=user.tenant_id,
        actor_type="user",
        actor_id=str(user.id),
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        request=ctx,
        data={"roles": roles},
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired refresh token.") from exc

    if claims.get("type") != "refresh":
        raise UnauthorizedError("A refresh token is required.")
    jti = claims.get("jti")
    if not jti or not auth_service.is_refresh_active(jti):
        raise UnauthorizedError("Refresh token has been revoked.")

    # Refresh tokens do not carry roles; reload them so a role change takes effect.
    import uuid

    from app.models.user import User

    user = db.get(User, uuid.UUID(claims["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User is no longer active.")
    roles = auth_service.get_user_role_names(db, user)

    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, roles=roles)
    return AccessTokenResponse(
        access_token=access, expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, request: Request, db: Session = Depends(get_db)) -> Response:
    ctx = get_request_context(request)
    try:
        claims = decode_token(payload.refresh_token)
        jti = claims.get("jti")
        tenant_id = claims.get("tenant_id")
        sub = claims.get("sub")
    except jwt.PyJWTError:
        # Logout is idempotent: an invalid token is treated as already logged out.
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if jti:
        auth_service.revoke_refresh_jti(jti)
    if tenant_id and sub:
        import uuid

        audit.record_event(
            db,
            tenant_id=uuid.UUID(tenant_id),
            actor_type="user",
            actor_id=sub,
            action="auth.logout",
            resource_type="user",
            resource_id=sub,
            request=ctx,
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
