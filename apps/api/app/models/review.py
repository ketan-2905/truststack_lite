"""Analyst review task (dashboard queue in MD 09)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import DecisionType, ReviewStatus
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class ReviewTask(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_tasks"

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
    status: Mapped[ReviewStatus] = mapped_column(
        pg_enum(ReviewStatus, "review_status"),
        nullable=False,
        default=ReviewStatus.open,
        index=True,
    )
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    decision: Mapped[DecisionType | None] = mapped_column(
        pg_enum(DecisionType, "decision_type"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
