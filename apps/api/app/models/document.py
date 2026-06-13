"""Uploaded identity document and its OCR/redaction artifacts (storage in MD 05)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import DocumentStatus, DocumentType
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.types import pg_enum


class Document(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "documents"

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
    doc_type: Mapped[DocumentType] = mapped_column(
        pg_enum(DocumentType, "document_type"), nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        pg_enum(DocumentStatus, "document_status"),
        nullable=False,
        default=DocumentStatus.uploaded,
        index=True,
    )
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    redacted_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
