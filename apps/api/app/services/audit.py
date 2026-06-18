"""Append-only audit event service.

Every sensitive operation routes through :func:`record_event`. Events are never
updated or deleted.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def record_event_committed(**kwargs) -> None:
    """Record an audit event in its own committed transaction.

    Used for security events that accompany an *error* response (failed login,
    forbidden access): the request's own session is rolled back when the error
    propagates, so those events must be persisted independently.
    """
    import app.db as app_db  # late import so test rebinding of SessionLocal applies

    with app_db.SessionLocal() as db:
        record_event(db, **kwargs)
        db.commit()


def record_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    tenant_id: uuid.UUID | None = None,
    actor_type: str = "system",
    actor_id: str | None = None,
    resource_id: str | None = None,
    case_id: uuid.UUID | None = None,
    request=None,  # app.deps.RequestContext | None
    data: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        case_id=case_id,
        request_id=getattr(request, "request_id", None),
        ip=getattr(request, "ip", None),
        user_agent=getattr(request, "user_agent", None),
        data=data,
    )
    db.add(event)
    db.flush()
    return event


def list_events(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action: str | None = None,
    resource_type: str | None = None,
    case_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[AuditEvent], int]:
    filters = [AuditEvent.tenant_id == tenant_id]
    if action:
        filters.append(AuditEvent.action == action)
    if resource_type:
        filters.append(AuditEvent.resource_type == resource_type)
    if case_id:
        filters.append(AuditEvent.case_id == case_id)

    total = db.scalar(select(func.count()).select_from(AuditEvent).where(*filters)) or 0
    stmt = (
        select(AuditEvent)
        .where(*filters)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all(), total
