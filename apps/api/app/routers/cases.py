"""Onboarding case endpoints (B2B, tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, WRITE_ROLES, Principal, require_roles
from app.schemas.case import CaseCreate, CaseOut
from app.services import audit
from app.services import cases as case_service
from app.services import events as event_service
from app.services import idempotency as idempotency_service

router = APIRouter(prefix="/v1/onboarding-cases", tags=["onboarding-cases"])


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    principal: Principal = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> CaseOut:
    # Idempotent creation for external clients: a repeated key returns the
    # originally created case rather than creating a duplicate.
    if idempotency_key:
        prior = idempotency_service.get(db, principal.tenant_id, idempotency_key)
        if prior is not None and prior.resource_id:
            existing = case_service.get_case(
                db, principal.tenant_id, uuid.UUID(prior.resource_id)
            )
            return CaseOut.model_validate(existing)

    case = case_service.create_case(db, principal.tenant_id, payload)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="case.created",
        resource_type="onboarding_case",
        resource_id=case.id,
        case_id=case.id,
        request=principal.request,
        data={"applicant_id": str(case.applicant_id)},
    )
    event_service.emit_event(
        db,
        tenant_id=principal.tenant_id,
        event_type=event_service.EVENT_CASE_CREATED,
        payload={"case_id": str(case.id), "applicant_id": str(case.applicant_id)},
        case_id=case.id,
    )
    if idempotency_key:
        idempotency_service.store(
            db,
            tenant_id=principal.tenant_id,
            key=idempotency_key,
            resource_type="onboarding_case",
            resource_id=str(case.id),
            response_code=201,
            response_body={"id": str(case.id)},
        )
    return CaseOut.model_validate(case)


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: uuid.UUID,
    principal: Principal = Depends(require_roles(*ALL_TENANT_ROLES)),
    db: Session = Depends(get_db),
) -> CaseOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    return CaseOut.model_validate(case)
