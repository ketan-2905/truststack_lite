"""Tenant API key management (dashboard, tenant_admin only).

API-key principals cannot manage keys: they hold the ``system`` role, not
``tenant_admin``, so they are rejected with 403 by ``require_roles``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import Principal, require_roles
from app.enums import RoleName
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedOut,
    ApiKeyOut,
    ApiKeyRotateRequest,
)
from app.services import api_keys as api_key_service
from app.services import audit

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])


def _created_out(api_key, raw_key: str) -> ApiKeyCreatedOut:
    base = ApiKeyOut.model_validate(api_key).model_dump()
    return ApiKeyCreatedOut(**base, raw_key=raw_key)


@router.post("", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreate,
    principal: Principal = Depends(require_roles(RoleName.tenant_admin)),
    db: Session = Depends(get_db),
) -> ApiKeyCreatedOut:
    api_key, raw = api_key_service.create_api_key(
        db,
        tenant_id=principal.tenant_id,
        name=payload.name,
        created_by_user_id=uuid.UUID(principal.actor_id) if principal.actor_id else None,
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="api_key.created",
        resource_type="tenant_api_key",
        resource_id=api_key.id,
        request=principal.request,
        data={"prefix": api_key.prefix, "name": api_key.name},
    )
    return _created_out(api_key, raw)


@router.get("", response_model=list[ApiKeyOut])
def list_api_keys(
    principal: Principal = Depends(require_roles(RoleName.tenant_admin)),
    db: Session = Depends(get_db),
) -> list[ApiKeyOut]:
    keys = api_key_service.list_api_keys(db, principal.tenant_id)
    return [ApiKeyOut.model_validate(k) for k in keys]


@router.post("/{key_id}/rotate", response_model=ApiKeyCreatedOut)
def rotate_api_key(
    key_id: uuid.UUID,
    payload: ApiKeyRotateRequest,
    principal: Principal = Depends(require_roles(RoleName.tenant_admin)),
    db: Session = Depends(get_db),
) -> ApiKeyCreatedOut:
    new_key, raw = api_key_service.rotate_api_key(
        db,
        tenant_id=principal.tenant_id,
        key_id=key_id,
        expire_old=payload.expire_old,
        created_by_user_id=uuid.UUID(principal.actor_id) if principal.actor_id else None,
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="api_key.rotated",
        resource_type="tenant_api_key",
        resource_id=new_key.id,
        request=principal.request,
        data={"rotated_from": str(key_id), "expire_old": payload.expire_old},
    )
    return _created_out(new_key, raw)


@router.post("/{key_id}/revoke", response_model=ApiKeyOut)
def revoke_api_key(
    key_id: uuid.UUID,
    principal: Principal = Depends(require_roles(RoleName.tenant_admin)),
    db: Session = Depends(get_db),
) -> ApiKeyOut:
    api_key = api_key_service.revoke_api_key(db, principal.tenant_id, key_id)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="api_key.revoked",
        resource_type="tenant_api_key",
        resource_id=api_key.id,
        request=principal.request,
    )
    return ApiKeyOut.model_validate(api_key)
