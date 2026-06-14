"""Risk signals (reason codes) and risk decisions (engine in MD 07)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import DecisionType, RiskSeverity
from app.models.base import Base, UUIDMixin
from app.models.types import pg_enum


class RiskSignal(UUIDMixin, Base):
    __tablename__ = "risk_signals"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[RiskSeverity] = mapped_column(
        pg_enum(RiskSeverity, "risk_severity"), nullable=False, index=True
    )
    weight: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


class RiskDecision(UUIDMixin, Base):
    __tablename__ = "risk_decisions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[DecisionType] = mapped_column(
        pg_enum(DecisionType, "decision_type"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    severity: Mapped[RiskSeverity] = mapped_column(
        pg_enum(RiskSeverity, "risk_severity"), nullable=False
    )
    reason_codes: Mapped[list] = mapped_column(JSONB, nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    explanation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    decided_by: Mapped[str] = mapped_column(String(32), nullable=False, default="system")
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
