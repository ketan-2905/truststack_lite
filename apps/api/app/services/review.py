"""Review task service (analyst queue). Full dashboard lands in MD 09."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import ReviewStatus
from app.models.review import ReviewTask


def ensure_open_review_task(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    priority: int = 0,
    notes: str | None = None,
) -> ReviewTask:
    """Create an open review task for the case if none is already open
    (idempotent — repeated risk recomputes do not pile up duplicate tasks)."""
    existing = db.scalar(
        select(ReviewTask).where(
            ReviewTask.tenant_id == tenant_id,
            ReviewTask.case_id == case_id,
            ReviewTask.status.in_([ReviewStatus.open, ReviewStatus.assigned]),
        )
    )
    if existing is not None:
        return existing
    task = ReviewTask(
        tenant_id=tenant_id,
        case_id=case_id,
        status=ReviewStatus.open,
        priority=priority,
        notes=notes,
    )
    db.add(task)
    db.flush()
    return task
