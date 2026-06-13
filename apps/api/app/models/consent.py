"""Consent notices (versioned) and consent records (immutable receipts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import ConsentType
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class ConsentNotice(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A versioned, localized consent notice. Activation is exclusive per
    (tenant, key, jurisdiction, language)."""

    __tablename__ = "consent_notices"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "key", "version", "language",
            name="uq_consent_notice_version",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    purposes: Mapped[list] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)


class ConsentRecord(UUIDMixin, Base):
    """Immutable consent receipt. Withdrawals are new records with granted=False;
    existing records are never mutated or deleted."""

    __tablename__ = "consent_records"

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
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consent_notices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        pg_enum(ConsentType, "consent_type"),
        nullable=False,
        default=ConsentType.applicant,
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notice_version: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(32), nullable=False)
    purposes: Mapped[list] = mapped_column(JSONB, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guardian_relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receipt_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
