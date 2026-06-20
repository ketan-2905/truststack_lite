"""Audit event read endpoint (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import ALL_TENANT_ROLES, Principal, require_roles
from app.schemas.audit import AuditEventOut
from app.schemas.common import Page
from app.services import audit as audit_service

router = APIRouter(prefix="/v1/audit-events", tags=["audit"])


@router.get("", response_model=Page[AuditEventOut])
def list_audit_events(
    principal: Principal = Depends(require_roles(*ALL_TENANT_ROLES)),
    db: Session = Depends(get_db),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    case_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[AuditEventOut]:
    items, total = audit_service.list_events(
        db,
        tenant_id=principal.tenant_id,
        action=action,
        resource_type=resource_type,
        case_id=case_id,
        limit=limit,
        offset=offset,
    )
    return Page[AuditEventOut](
        items=[AuditEventOut.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )
