"""Retention/erasure request schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.enums import RetentionRequestState
from app.schemas.common import ORMModel


class RetentionRequestCreate(BaseModel):
    applicant_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    reason: str | None = None


class RetentionStateUpdate(BaseModel):
    state: RetentionRequestState


class RetentionRequestOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    applicant_id: uuid.UUID | None
    case_id: uuid.UUID | None
    state: RetentionRequestState
    reason: str | None
    requested_by_user_id: uuid.UUID | None
    approved_by_user_id: uuid.UUID | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
