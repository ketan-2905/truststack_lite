"""Risk signal and decision schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.enums import DecisionType, RiskSeverity
from app.schemas.common import ORMModel


class RiskSignalOut(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID
    code: str
    description: str
    severity: RiskSeverity
    weight: Decimal
    evidence: dict | None
    policy_version: str | None
    created_at: datetime


class RiskDecisionOut(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID
    decision: DecisionType
    score: Decimal
    severity: RiskSeverity
    reason_codes: list
    explanation: dict | None
    policy_version: str | None
    decided_by: str
    created_at: datetime


class RiskSummaryOut(ORMModel):
    decision: RiskDecisionOut | None
    signals: list[RiskSignalOut]
