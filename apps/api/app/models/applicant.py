"""Applicant model — the person being onboarded."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Applicant(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "applicants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_ref", name="uq_applicants_tenant_external_ref"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
