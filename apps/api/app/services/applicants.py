"""Applicant repository/service (tenant-scoped)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.applicant import Applicant
from app.schemas.applicant import ApplicantCreate


def create_applicant(db: Session, tenant_id: uuid.UUID, payload: ApplicantCreate) -> Applicant:
    applicant = Applicant(
        tenant_id=tenant_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        external_ref=payload.external_ref,
        date_of_birth=payload.date_of_birth,
        attributes=payload.attributes,
    )
    db.add(applicant)
    db.flush()
    return applicant


def get_applicant(db: Session, tenant_id: uuid.UUID, applicant_id: uuid.UUID) -> Applicant:
    stmt = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == tenant_id,
        Applicant.deleted_at.is_(None),
    )
    applicant = db.scalar(stmt)
    if applicant is None:
        raise NotFoundError("Applicant")
    return applicant
