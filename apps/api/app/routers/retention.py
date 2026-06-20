"""Retention / erasure request endpoints (DPDP-style data subject requests)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, Principal, require_roles
from app.enums import RetentionRequestState, RoleName
from app.schemas.retention import (
    RetentionRequestCreate,
    RetentionRequestOut,
    RetentionStateUpdate,
)
from app.services import audit
from app.services import retention as retention_service

router = APIRouter(prefix="/v1/retention-requests", tags=["retention"])

REQUESTER = require_roles(RoleName.tenant_admin, RoleName.system, RoleName.analyst)
READER = require_roles(*ALL_TENANT_ROLES)
APPROVER = require_roles(RoleName.tenant_admin)


def _user_id(principal: Principal) -> uuid.UUID | None:
    if principal.actor_type == "user" and principal.actor_id:
        return uuid.UUID(principal.actor_id)
    return None


@router.post("", response_model=RetentionRequestOut, status_code=status.HTTP_201_CREATED)
def create_retention_request(
    payload: RetentionRequestCreate,
    principal: Principal = Depends(REQUESTER),
    db: Session = Depends(get_db),
) -> RetentionRequestOut:
    request = retention_service.create_request(
        db,
        tenant_id=principal.tenant_id,
        payload=payload,
        requested_by_user_id=_user_id(principal),
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="retention_request.created",
        resource_type="retention_request",
        resource_id=request.id,
        case_id=request.case_id,
        request=principal.request,
        data={"applicant_id": str(request.applicant_id) if request.applicant_id else None},
    )
    return RetentionRequestOut.model_validate(request)


@router.get("", response_model=list[RetentionRequestOut])
def list_retention_requests(
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
    state: RetentionRequestState | None = Query(default=None),
) -> list[RetentionRequestOut]:
    requests = retention_service.list_requests(db, principal.tenant_id, state=state)
    return [RetentionRequestOut.model_validate(r) for r in requests]


@router.get("/{request_id}", response_model=RetentionRequestOut)
def get_retention_request(
    request_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> RetentionRequestOut:
    request = retention_service.get_request(db, principal.tenant_id, request_id)
    return RetentionRequestOut.model_validate(request)


@router.post("/{request_id}/state", response_model=RetentionRequestOut)
def update_retention_state(
    request_id: uuid.UUID,
    payload: RetentionStateUpdate,
    principal: Principal = Depends(APPROVER),
    db: Session = Depends(get_db),
) -> RetentionRequestOut:
    request = retention_service.update_state(
        db,
        tenant_id=principal.tenant_id,
        request_id=request_id,
        new_state=payload.state,
        approved_by_user_id=_user_id(principal),
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action=f"retention_request.{payload.state.value}",
        resource_type="retention_request",
        resource_id=request.id,
        case_id=request.case_id,
        request=principal.request,
    )
    return RetentionRequestOut.model_validate(request)
