"""Deterministic seed data.

Creates exactly one tenant, a tenant admin, an analyst, an applicant, and one
active consent notice — all with fixed UUIDs so the seed is idempotent and
reproducible. Passwords come from SEED_* env vars and are stored Argon2-hashed.

Run inside the api container:  python -m app.seed
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.enums import RoleName
from app.hashing import canonical_hash
from app.logging_config import configure_logging, get_logger
from app.models.applicant import Applicant
from app.models.consent import ConsentNotice
from app.models.role import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.security import hash_password

logger = get_logger("truststack.seed")

# Fixed identifiers keep the seed deterministic and idempotent.
SEED_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SEED_ADMIN_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
SEED_ANALYST_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")
SEED_APPLICANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000004")
SEED_NOTICE_ID = uuid.UUID("00000000-0000-4000-8000-000000000005")

NOTICE_KEY = "onboarding-default"
NOTICE_PURPOSES = ["identity_verification", "fraud_prevention", "regulatory_compliance"]


def seed_roles(db: Session) -> dict[RoleName, Role]:
    roles: dict[RoleName, Role] = {}
    for name in RoleName:
        role = db.query(Role).filter(Role.name == name).one_or_none()
        if role is None:
            role = Role(name=name, description=f"{name.value} role")
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


def _get_or_create_user(
    db: Session,
    user_id: uuid.UUID,
    email: str,
    password: str,
    full_name: str,
    role: Role,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            tenant_id=SEED_TENANT_ID,
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            is_active=True,
        )
        db.add(user)
        db.flush()
    if not any(ur.role_id == role.id for ur in user.roles):
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.flush()
    return user


def seed_tenant(db: Session) -> Tenant:
    tenant = db.get(Tenant, SEED_TENANT_ID)
    if tenant is None:
        tenant = Tenant(
            id=SEED_TENANT_ID,
            name=settings.seed_tenant_name,
            slug=settings.seed_tenant_slug,
            status="active",
        )
        db.add(tenant)
        db.flush()
    return tenant


def seed_applicant(db: Session) -> Applicant:
    applicant = db.get(Applicant, SEED_APPLICANT_ID)
    if applicant is None:
        applicant = Applicant(
            id=SEED_APPLICANT_ID,
            tenant_id=SEED_TENANT_ID,
            full_name="Asha Verma",
            email="asha.verma@example.com",
            phone="+91-9000000000",
            external_ref="seed-applicant-1",
            date_of_birth=date(1995, 7, 14),
        )
        db.add(applicant)
        db.flush()
    return applicant


def seed_consent_notice(db: Session) -> ConsentNotice:
    notice = db.get(ConsentNotice, SEED_NOTICE_ID)
    if notice is None:
        language = settings.languages[0] if settings.languages else "en"
        title = "Onboarding Consent Notice"
        body = (
            "We process the identity documents and personal data you provide "
            "solely to verify your identity, prevent fraud, and meet regulatory "
            "obligations. This is placeholder text pending legal review; no DPDP "
            "compliance is claimed without such review."
        )
        content_hash = canonical_hash(
            {
                "key": NOTICE_KEY,
                "version": 1,
                "jurisdiction": settings.default_jurisdiction,
                "language": language,
                "title": title,
                "body": body,
                "purposes": NOTICE_PURPOSES,
            }
        )
        notice = ConsentNotice(
            id=SEED_NOTICE_ID,
            tenant_id=SEED_TENANT_ID,
            key=NOTICE_KEY,
            version=1,
            jurisdiction=settings.default_jurisdiction,
            language=language,
            title=title,
            body=body,
            purposes=NOTICE_PURPOSES,
            content_hash=content_hash,
            is_active=True,
        )
        db.add(notice)
        db.flush()
    return notice


def seed_all(db: Session) -> None:
    roles = seed_roles(db)
    seed_tenant(db)
    _get_or_create_user(
        db,
        SEED_ADMIN_ID,
        settings.seed_admin_email,
        settings.seed_admin_password,
        "Tenant Admin",
        roles[RoleName.tenant_admin],
    )
    _get_or_create_user(
        db,
        SEED_ANALYST_ID,
        settings.seed_analyst_email,
        settings.seed_analyst_password,
        "Analyst",
        roles[RoleName.analyst],
    )
    seed_applicant(db)
    seed_consent_notice(db)


def main() -> None:
    configure_logging(settings.log_level)
    with SessionLocal() as db:
        seed_all(db)
        db.commit()
    logger.info(
        "seed_complete",
        extra={"fields": {
            "tenant_id": str(SEED_TENANT_ID),
            "admin_email": settings.seed_admin_email,
            "analyst_email": settings.seed_analyst_email,
            "applicant_id": str(SEED_APPLICANT_ID),
            "consent_notice_id": str(SEED_NOTICE_ID),
        }},
    )
    print(
        "Seed complete:\n"
        f"  tenant_id   = {SEED_TENANT_ID}\n"
        f"  admin       = {settings.seed_admin_email}\n"
        f"  analyst     = {settings.seed_analyst_email}\n"
        f"  applicant   = {SEED_APPLICANT_ID}\n"
        f"  consent     = {SEED_NOTICE_ID} (key={NOTICE_KEY}, v1, active)"
    )


if __name__ == "__main__":
    main()
