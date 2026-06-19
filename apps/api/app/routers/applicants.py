"""Applicant endpoints (B2B, tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, WRITE_ROLES, Principal, require_roles
from app.schemas.applicant import ApplicantCreate, ApplicantOut
from app.services import applicants as applicant_service
from app.services import audit

router = APIRouter(prefix="/v1/applicants", tags=["applicants"])


@router.post("", response_model=ApplicantOut, status_code=status.HTTP_201_CREATED)
def create_applicant(
    payload: ApplicantCreate,
    principal: Principal = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ApplicantOut:
    applicant = applicant_service.create_applicant(db, principal.tenant_id, payload)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="applicant.created",
        resource_type="applicant",
        resource_id=applicant.id,
        request=principal.request,
        data={"external_ref": applicant.external_ref},
    )
    return ApplicantOut.model_validate(applicant)


@router.get("/{applicant_id}", response_model=ApplicantOut)
def get_applicant(
    applicant_id: uuid.UUID,
    principal: Principal = Depends(require_roles(*ALL_TENANT_ROLES)),
    db: Session = Depends(get_db),
) -> ApplicantOut:
    applicant = applicant_service.get_applicant(db, principal.tenant_id, applicant_id)
    return ApplicantOut.model_validate(applicant)
