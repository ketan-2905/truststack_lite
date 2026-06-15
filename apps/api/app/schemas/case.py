"""Onboarding case schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.enums import CaseState, RiskSeverity
from app.schemas.common import ORMModel


class CaseCreate(BaseModel):
    applicant_id: uuid.UUID
    reference: str | None = Field(default=None, max_length=64)
    attributes: dict | None = None


class CaseOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    applicant_id: uuid.UUID
    reference: str | None
    state: CaseState
    risk_score: Decimal | None
    risk_severity: RiskSeverity | None
    attributes: dict | None
    created_at: datetime
    updated_at: datetime
