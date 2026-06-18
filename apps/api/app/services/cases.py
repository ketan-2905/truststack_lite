"""Onboarding case repository/service (tenant-scoped)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import CaseState
from app.errors import NotFoundError
from app.models.onboarding_case import OnboardingCase
from app.schemas.case import CaseCreate
from app.services.applicants import get_applicant


def create_case(
    db: Session,
    tenant_id: uuid.UUID,
    payload: CaseCreate,
    created_by_user_id: uuid.UUID | None = None,
) -> OnboardingCase:
    # Enforce that the applicant belongs to this tenant before linking the case.
    get_applicant(db, tenant_id, payload.applicant_id)

    case = OnboardingCase(
        tenant_id=tenant_id,
        applicant_id=payload.applicant_id,
        reference=payload.reference,
        state=CaseState.created,
        created_by_user_id=created_by_user_id,
        attributes=payload.attributes,
    )
    db.add(case)
    db.flush()
    return case


def get_case(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> OnboardingCase:
    stmt = select(OnboardingCase).where(
        OnboardingCase.id == case_id,
        OnboardingCase.tenant_id == tenant_id,
        OnboardingCase.deleted_at.is_(None),
    )
    case = db.scalar(stmt)
    if case is None:
        raise NotFoundError("Onboarding case")
    return case
