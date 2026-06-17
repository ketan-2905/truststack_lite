"""Consent ledger service.

Consent is a versioned, immutable ledger:
- Notices are versioned and activated exclusively per (key, jurisdiction, language).
- Each grant/withdrawal is a new, immutable ``ConsentRecord`` with a receipt hash.
- A case cannot be submitted (or, in MD 05, have documents uploaded) until the
  required consent exists — guardian consent is additionally required for minors.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import ConsentType
from app.errors import ConflictError, ConsentRequiredError, NotFoundError
from app.hashing import canonical_hash
from app.models.applicant import Applicant
from app.models.consent import ConsentNotice, ConsentRecord
from app.models.onboarding_case import OnboardingCase
from app.schemas.consent import ConsentNoticeCreate


def _now() -> datetime:
    return datetime.now(UTC)


# ── Notices ──────────────────────────────────────────────────────────────────
def create_notice(
    db: Session, tenant_id: uuid.UUID, payload: ConsentNoticeCreate
) -> ConsentNotice:
    existing = db.scalar(
        select(ConsentNotice).where(
            ConsentNotice.tenant_id == tenant_id,
            ConsentNotice.key == payload.key,
            ConsentNotice.version == payload.version,
            ConsentNotice.language == payload.language,
            ConsentNotice.deleted_at.is_(None),
        )
    )
    if existing is not None:
        raise ConflictError(
            f"Notice {payload.key} v{payload.version} ({payload.language}) already exists."
        )

    content_hash = canonical_hash(
        {
            "key": payload.key,
            "version": payload.version,
            "jurisdiction": payload.jurisdiction,
            "language": payload.language,
            "title": payload.title,
            "body": payload.body,
            "purposes": payload.purposes,
        }
    )
    notice = ConsentNotice(
        tenant_id=tenant_id,
        key=payload.key,
        version=payload.version,
        jurisdiction=payload.jurisdiction,
        language=payload.language,
        title=payload.title,
        body=payload.body,
        purposes=payload.purposes,
        content_hash=content_hash,
        is_active=False,
    )
    db.add(notice)
    db.flush()
    return notice


def get_notice(db: Session, tenant_id: uuid.UUID, notice_id: uuid.UUID) -> ConsentNotice:
    notice = db.scalar(
        select(ConsentNotice).where(
            ConsentNotice.id == notice_id,
            ConsentNotice.tenant_id == tenant_id,
            ConsentNotice.deleted_at.is_(None),
        )
    )
    if notice is None:
        raise NotFoundError("Consent notice")
    return notice


def list_notices(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    jurisdiction: str | None = None,
    language: str | None = None,
    active_only: bool = False,
) -> list[ConsentNotice]:
    stmt = select(ConsentNotice).where(
        ConsentNotice.tenant_id == tenant_id, ConsentNotice.deleted_at.is_(None)
    )
    if jurisdiction:
        stmt = stmt.where(ConsentNotice.jurisdiction == jurisdiction)
    if language:
        stmt = stmt.where(ConsentNotice.language == language)
    if active_only:
        stmt = stmt.where(ConsentNotice.is_active.is_(True))
    stmt = stmt.order_by(ConsentNotice.created_at.desc())
    return list(db.scalars(stmt).all())


def set_notice_active(
    db: Session, tenant_id: uuid.UUID, notice_id: uuid.UUID, active: bool
) -> ConsentNotice:
    notice = get_notice(db, tenant_id, notice_id)
    if active:
        # Exclusive activation: deactivate siblings sharing key/jurisdiction/language.
        siblings = db.scalars(
            select(ConsentNotice).where(
                ConsentNotice.tenant_id == tenant_id,
                ConsentNotice.key == notice.key,
                ConsentNotice.jurisdiction == notice.jurisdiction,
                ConsentNotice.language == notice.language,
                ConsentNotice.id != notice.id,
                ConsentNotice.is_active.is_(True),
            )
        ).all()
        for sibling in siblings:
            sibling.is_active = False
    notice.is_active = active
    db.flush()
    return notice


def get_active_notice(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    jurisdiction: str,
    language: str,
    key: str | None = None,
) -> ConsentNotice | None:
    stmt = select(ConsentNotice).where(
        ConsentNotice.tenant_id == tenant_id,
        ConsentNotice.jurisdiction == jurisdiction,
        ConsentNotice.language == language,
        ConsentNotice.is_active.is_(True),
        ConsentNotice.deleted_at.is_(None),
    )
    if key:
        stmt = stmt.where(ConsentNotice.key == key)
    stmt = stmt.order_by(ConsentNotice.version.desc())
    return db.scalar(stmt)


# ── Minors ───────────────────────────────────────────────────────────────────
def compute_age(dob: date, on_date: date) -> int:
    return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))


def is_minor(applicant: Applicant, on_date: date | None = None) -> bool:
    if applicant.date_of_birth is None:
        return False
    return compute_age(applicant.date_of_birth, on_date or _now().date()) < 18


# ── Receipts (immutable) ─────────────────────────────────────────────────────
def record_consent(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case: OnboardingCase,
    applicant: Applicant,
    notice: ConsentNotice,
    granted: bool,
    consent_type: ConsentType,
    guardian_name: str | None = None,
    guardian_relationship: str | None = None,
    source_ip: str | None = None,
    user_agent: str | None = None,
) -> ConsentRecord:
    if consent_type == ConsentType.guardian and granted and not guardian_name:
        raise ConflictError("guardian_name is required for guardian consent.")

    record_id = uuid.uuid4()
    created_at = _now()
    receipt_hash = canonical_hash(
        {
            "record_id": str(record_id),
            "tenant_id": str(tenant_id),
            "case_id": str(case.id),
            "applicant_id": str(applicant.id),
            "notice_id": str(notice.id),
            "notice_version": notice.version,
            "notice_content_hash": notice.content_hash,
            "granted": granted,
            "consent_type": consent_type.value,
            "language": notice.language,
            "jurisdiction": notice.jurisdiction,
            "purposes": notice.purposes,
            "guardian_name": guardian_name,
            "source_ip": source_ip,
            "user_agent": user_agent,
            "created_at": created_at.isoformat(),
        }
    )
    record = ConsentRecord(
        id=record_id,
        tenant_id=tenant_id,
        case_id=case.id,
        applicant_id=applicant.id,
        notice_id=notice.id,
        consent_type=consent_type,
        granted=granted,
        notice_version=notice.version,
        language=notice.language,
        jurisdiction=notice.jurisdiction,
        purposes=notice.purposes,
        source_ip=source_ip,
        user_agent=user_agent,
        guardian_name=guardian_name,
        guardian_relationship=guardian_relationship,
        receipt_hash=receipt_hash,
        created_at=created_at,
    )
    db.add(record)
    db.flush()
    return record


def get_timeline(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> list[ConsentRecord]:
    stmt = (
        select(ConsentRecord)
        .where(ConsentRecord.tenant_id == tenant_id, ConsentRecord.case_id == case_id)
        .order_by(ConsentRecord.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def _latest_by_type(db: Session, case_id: uuid.UUID) -> dict[ConsentType, ConsentRecord]:
    records = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.case_id == case_id)
        .order_by(ConsentRecord.created_at.asc())
    ).all()
    latest: dict[ConsentType, ConsentRecord] = {}
    for record in records:
        latest[record.consent_type] = record  # later records overwrite earlier
    return latest


def applicant_consent_granted(db: Session, case_id: uuid.UUID) -> bool:
    latest = _latest_by_type(db, case_id).get(ConsentType.applicant)
    return bool(latest and latest.granted)


def guardian_consent_granted(db: Session, case_id: uuid.UUID) -> bool:
    latest = _latest_by_type(db, case_id).get(ConsentType.guardian)
    return bool(latest and latest.granted)


def case_consent_satisfied(db: Session, applicant: Applicant, case: OnboardingCase) -> bool:
    latest = _latest_by_type(db, case.id)
    applicant_consent = latest.get(ConsentType.applicant)
    if applicant_consent is None or not applicant_consent.granted:
        return False
    if is_minor(applicant):
        guardian_consent = latest.get(ConsentType.guardian)
        if guardian_consent is None or not guardian_consent.granted:
            return False
    return True


def ensure_case_consent(db: Session, applicant: Applicant, case: OnboardingCase) -> None:
    """Raise 409 Consent Required if the case lacks the required consent."""
    latest = _latest_by_type(db, case.id)
    applicant_consent = latest.get(ConsentType.applicant)
    if applicant_consent is None or not applicant_consent.granted:
        raise ConsentRequiredError("Applicant consent is required before proceeding.")
    if is_minor(applicant):
        guardian_consent = latest.get(ConsentType.guardian)
        if guardian_consent is None or not guardian_consent.granted:
            raise ConsentRequiredError(
                "Guardian consent is required for a minor applicant before proceeding."
            )
