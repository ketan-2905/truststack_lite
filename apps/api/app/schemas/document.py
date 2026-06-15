"""Document schemas (safe — raw OCR/PII is never exposed by default)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.enums import DocumentStatus, DocumentType
from app.models.document import Document


class DocumentOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID
    applicant_id: uuid.UUID
    doc_type: DocumentType
    status: DocumentStatus
    mime_type: str | None
    size_bytes: int | None
    content_sha256: str | None
    has_redacted_preview: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, document: Document) -> DocumentOut:
        return cls(
            id=document.id,
            tenant_id=document.tenant_id,
            case_id=document.case_id,
            applicant_id=document.applicant_id,
            doc_type=document.doc_type,
            status=document.status,
            mime_type=document.mime_type,
            size_bytes=document.size_bytes,
            content_sha256=document.content_sha256,
            has_redacted_preview=document.redacted_storage_key is not None,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
