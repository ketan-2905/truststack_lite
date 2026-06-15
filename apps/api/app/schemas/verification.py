"""Verification step schemas (safe — no raw provider identity payloads)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.enums import VerificationStepStatus, VerificationStepType
from app.schemas.common import ORMModel


class VerificationStartRequest(BaseModel):
    step_type: VerificationStepType = VerificationStepType.document_authenticity


class VerificationStepOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID
    step_type: VerificationStepType
    status: VerificationStepStatus
    provider: str | None
    provider_ref: str | None
    response_hash: str | None
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
