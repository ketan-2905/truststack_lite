"""Consent notice management and public notice fetch."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, Principal, require_roles
from app.enums import RoleName
from app.errors import NotFoundError
from app.schemas.consent import (
    ConsentNoticeCreate,
    ConsentNoticeOut,
    ConsentNoticePublicOut,
)
from app.services import audit
from app.services import consent as consent_service
from app.services import tenants as tenant_service

router = APIRouter(tags=["consent-notices"])

ADMIN = require_roles(RoleName.tenant_admin)
READER = require_roles(*ALL_TENANT_ROLES)


@router.post(
    "/v1/consent-notices",
    response_model=ConsentNoticeOut,
    status_code=status.HTTP_201_CREATED,
)
def create_notice(
    payload: ConsentNoticeCreate,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> ConsentNoticeOut:
    notice = consent_service.create_notice(db, principal.tenant_id, payload)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="consent_notice.created",
        resource_type="consent_notice",
        resource_id=notice.id,
        request=principal.request,
        data={"key": notice.key, "version": notice.version, "language": notice.language},
    )
    return ConsentNoticeOut.model_validate(notice)


@router.get("/v1/consent-notices", response_model=list[ConsentNoticeOut])
def list_notices(
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
    jurisdiction: str | None = Query(default=None),
    language: str | None = Query(default=None),
    active_only: bool = Query(default=False),
) -> list[ConsentNoticeOut]:
    notices = consent_service.list_notices(
        db,
        principal.tenant_id,
        jurisdiction=jurisdiction,
        language=language,
        active_only=active_only,
    )
    return [ConsentNoticeOut.model_validate(n) for n in notices]


@router.post("/v1/consent-notices/{notice_id}/activate", response_model=ConsentNoticeOut)
def activate_notice(
    notice_id: uuid.UUID,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> ConsentNoticeOut:
    notice = consent_service.set_notice_active(db, principal.tenant_id, notice_id, True)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="consent_notice.activated",
        resource_type="consent_notice",
        resource_id=notice.id,
        request=principal.request,
    )
    return ConsentNoticeOut.model_validate(notice)


@router.post("/v1/consent-notices/{notice_id}/deactivate", response_model=ConsentNoticeOut)
def deactivate_notice(
    notice_id: uuid.UUID,
    principal: Principal = Depends(ADMIN),
    db: Session = Depends(get_db),
) -> ConsentNoticeOut:
    notice = consent_service.set_notice_active(db, principal.tenant_id, notice_id, False)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="consent_notice.deactivated",
        resource_type="consent_notice",
        resource_id=notice.id,
        request=principal.request,
    )
    return ConsentNoticeOut.model_validate(notice)


# ── Public, unauthenticated notice fetch (applicant-facing) ──────────────────
@router.get("/v1/public/consent-notices/active", response_model=ConsentNoticePublicOut)
def public_active_notice(
    db: Session = Depends(get_db),
    tenant_slug: str = Query(...),
    jurisdiction: str = Query(...),
    language: str = Query(...),
    key: str | None = Query(default=None),
) -> ConsentNoticePublicOut:
    tenant = tenant_service.get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise NotFoundError("Tenant")
    notice = consent_service.get_active_notice(
        db, tenant.id, jurisdiction=jurisdiction, language=language, key=key
    )
    if notice is None:
        raise NotFoundError("Active consent notice")
    return ConsentNoticePublicOut.model_validate(notice)
