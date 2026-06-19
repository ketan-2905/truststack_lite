"""Consent receipts, withdrawal, consent gate, and consent timeline."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, Principal, require_roles
from app.enums import CaseState, ConsentType, RoleName
from app.schemas.case import CaseOut
from app.schemas.consent import ConsentGrant, ConsentRecordOut, ConsentWithdraw
from app.services import applicants as applicant_service
from app.services import audit
from app.services import cases as case_service
from app.services import consent as consent_service

router = APIRouter(prefix="/v1/onboarding-cases", tags=["consent"])

RECORDER = require_roles(RoleName.tenant_admin, RoleName.system, RoleName.analyst)
READER = require_roles(*ALL_TENANT_ROLES)
SUBMITTER = require_roles(RoleName.tenant_admin, RoleName.system)


@router.post(
    "/{case_id}/consents",
    response_model=ConsentRecordOut,
    status_code=status.HTTP_201_CREATED,
)
def record_consent(
    case_id: uuid.UUID,
    payload: ConsentGrant,
    principal: Principal = Depends(RECORDER),
    db: Session = Depends(get_db),
) -> ConsentRecordOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    applicant = applicant_service.get_applicant(db, principal.tenant_id, case.applicant_id)
    notice = consent_service.get_notice(db, principal.tenant_id, payload.notice_id)

    ctx = principal.request
    record = consent_service.record_consent(
        db,
        tenant_id=principal.tenant_id,
        case=case,
        applicant=applicant,
        notice=notice,
        granted=payload.granted,
        consent_type=payload.consent_type,
        guardian_name=payload.guardian_name,
        guardian_relationship=payload.guardian_relationship,
        source_ip=ctx.ip if ctx else None,
        user_agent=ctx.user_agent if ctx else None,
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="consent.granted" if payload.granted else "consent.withdrawn",
        resource_type="consent_record",
        resource_id=record.id,
        case_id=case.id,
        request=ctx,
        data={
            "notice_id": str(notice.id),
            "consent_type": payload.consent_type.value,
            "granted": payload.granted,
            "receipt_hash": record.receipt_hash,
        },
    )
    return ConsentRecordOut.model_validate(record)


@router.post(
    "/{case_id}/consents/withdraw",
    response_model=ConsentRecordOut,
    status_code=status.HTTP_201_CREATED,
)
def withdraw_consent(
    case_id: uuid.UUID,
    payload: ConsentWithdraw,
    principal: Principal = Depends(RECORDER),
    db: Session = Depends(get_db),
) -> ConsentRecordOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    applicant = applicant_service.get_applicant(db, principal.tenant_id, case.applicant_id)
    notice = consent_service.get_notice(db, principal.tenant_id, payload.notice_id)

    ctx = principal.request
    # Withdrawal is a NEW immutable record with granted=False — never a delete.
    record = consent_service.record_consent(
        db,
        tenant_id=principal.tenant_id,
        case=case,
        applicant=applicant,
        notice=notice,
        granted=False,
        consent_type=ConsentType.applicant,
        source_ip=ctx.ip if ctx else None,
        user_agent=ctx.user_agent if ctx else None,
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="consent.withdrawn",
        resource_type="consent_record",
        resource_id=record.id,
        case_id=case.id,
        request=ctx,
        data={"notice_id": str(notice.id), "reason": payload.reason},
    )
    return ConsentRecordOut.model_validate(record)


@router.get("/{case_id}/consents", response_model=list[ConsentRecordOut])
def consent_timeline(
    case_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> list[ConsentRecordOut]:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    records = consent_service.get_timeline(db, principal.tenant_id, case.id)
    return [ConsentRecordOut.model_validate(r) for r in records]


@router.post("/{case_id}/submit", response_model=CaseOut)
def submit_case(
    case_id: uuid.UUID,
    principal: Principal = Depends(SUBMITTER),
    db: Session = Depends(get_db),
) -> CaseOut:
    """Advance a case past intake. Blocked with 409 until required consent exists.

    Document upload (MD 05) reuses ``ensure_case_consent`` so the same gate
    protects uploads.
    """
    case = case_service.get_case(db, principal.tenant_id, case_id)
    applicant = applicant_service.get_applicant(db, principal.tenant_id, case.applicant_id)

    consent_service.ensure_case_consent(db, applicant, case)

    case.state = CaseState.documents_pending
    db.flush()
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="case.submitted",
        resource_type="onboarding_case",
        resource_id=case.id,
        case_id=case.id,
        request=principal.request,
    )
    return CaseOut.model_validate(case)
