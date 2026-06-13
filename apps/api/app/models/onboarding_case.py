"""Onboarding case — the unit of work that flows through the system."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import CaseState, RiskSeverity
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class OnboardingCase(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "onboarding_cases"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    state: Mapped[CaseState] = mapped_column(
        pg_enum(CaseState, "case_state"),
        nullable=False,
        default=CaseState.created,
        index=True,
    )
    risk_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    risk_severity: Mapped[RiskSeverity | None] = mapped_column(
        pg_enum(RiskSeverity, "risk_severity"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
