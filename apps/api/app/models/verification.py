"""Verification step — one provider call against a case (real providers in MD 06)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import VerificationStepStatus, VerificationStepType
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class VerificationStep(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "verification_steps"

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
    step_type: Mapped[VerificationStepType] = mapped_column(
        pg_enum(VerificationStepType, "verification_step_type"), nullable=False, index=True
    )
    status: Mapped[VerificationStepStatus] = mapped_column(
        pg_enum(VerificationStepStatus, "verification_step_status"),
        nullable=False,
        default=VerificationStepStatus.pending,
        index=True,
    )
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # External provider's session/inquiry id and a hash of its raw response, for
    # traceability without storing sensitive raw identity data.
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
