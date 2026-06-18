"""Retention / erasure request service with an explicit state machine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import RetentionRequestState
from app.errors import ConflictError, NotFoundError
from app.models.retention import RetentionRequest
from app.schemas.retention import RetentionRequestCreate

# Allowed transitions for a retention request.
_TRANSITIONS: dict[RetentionRequestState, set[RetentionRequestState]] = {
    RetentionRequestState.requested: {
        RetentionRequestState.approved,
        RetentionRequestState.rejected,
    },
    RetentionRequestState.approved: {RetentionRequestState.completed},
    RetentionRequestState.rejected: set(),
    RetentionRequestState.completed: set(),
}


def create_request(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    payload: RetentionRequestCreate,
    requested_by_user_id: uuid.UUID | None = None,
) -> RetentionRequest:
    request = RetentionRequest(
        tenant_id=tenant_id,
        applicant_id=payload.applicant_id,
        case_id=payload.case_id,
        state=RetentionRequestState.requested,
        reason=payload.reason,
        requested_by_user_id=requested_by_user_id,
    )
    db.add(request)
    db.flush()
    return request


def get_request(db: Session, tenant_id: uuid.UUID, request_id: uuid.UUID) -> RetentionRequest:
    request = db.scalar(
        select(RetentionRequest).where(
            RetentionRequest.id == request_id, RetentionRequest.tenant_id == tenant_id
        )
    )
    if request is None:
        raise NotFoundError("Retention request")
    return request


def list_requests(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    state: RetentionRequestState | None = None,
) -> list[RetentionRequest]:
    stmt = select(RetentionRequest).where(RetentionRequest.tenant_id == tenant_id)
    if state:
        stmt = stmt.where(RetentionRequest.state == state)
    stmt = stmt.order_by(RetentionRequest.created_at.desc())
    return list(db.scalars(stmt).all())


def update_state(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request_id: uuid.UUID,
    new_state: RetentionRequestState,
    approved_by_user_id: uuid.UUID | None = None,
) -> RetentionRequest:
    request = get_request(db, tenant_id, request_id)
    if new_state not in _TRANSITIONS[request.state]:
        raise ConflictError(
            f"Invalid transition {request.state.value} -> {new_state.value}."
        )
    request.state = new_state
    if new_state == RetentionRequestState.approved:
        request.approved_by_user_id = approved_by_user_id
    if new_state == RetentionRequestState.completed:
        request.completed_at = datetime.now(UTC)
    db.flush()
    return request
