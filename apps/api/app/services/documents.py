"""Document storage service.

Files are stored in object storage (never as DB blobs). The DB row holds
metadata: case/applicant, doc_type, mime, storage key, SHA-256 checksum, size,
and processing status. A duplicate-checksum across different applicants raises a
risk signal.
"""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import DocumentStatus, DocumentType, RiskSeverity
from app.errors import ConflictError, NotFoundError
from app.models.applicant import Applicant
from app.models.document import Document
from app.models.onboarding_case import OnboardingCase
from app.services import risk as risk_service
from app.storage import get_object, put_object

# Allowed upload types and limits.
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "application/pdf"}
IMAGE_MIME_TYPES = {"image/png", "image/jpeg"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB

DUPLICATE_CHECKSUM_CODE = "duplicate_artifact"


def _storage_key(tenant_id: uuid.UUID, case_id: uuid.UUID, document_id: uuid.UUID, filename: str) -> str:
    safe_name = filename.replace("/", "_").strip() or "upload"
    return f"{tenant_id}/{case_id}/{document_id}/original/{safe_name}"


def redacted_key(document: Document) -> str:
    return f"{document.tenant_id}/{document.case_id}/{document.id}/redacted/redacted.png"


def create_document(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case: OnboardingCase,
    applicant: Applicant,
    doc_type: DocumentType,
    filename: str,
    content: bytes,
    mime_type: str,
) -> Document:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ConflictError(
            f"Unsupported file type '{mime_type}'. Allowed: {sorted(ALLOWED_MIME_TYPES)}."
        )
    if not content:
        raise ConflictError("Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ConflictError(
            f"File exceeds maximum size of {MAX_UPLOAD_BYTES} bytes."
        )

    checksum = hashlib.sha256(content).hexdigest()
    document_id = uuid.uuid4()
    storage_key = _storage_key(tenant_id, case.id, document_id, filename)

    # Store in real object storage before persisting the row.
    put_object(storage_key, content, content_type=mime_type)

    document = Document(
        id=document_id,
        tenant_id=tenant_id,
        case_id=case.id,
        applicant_id=applicant.id,
        doc_type=doc_type,
        status=DocumentStatus.uploaded,
        storage_key=storage_key,
        content_sha256=checksum,
        mime_type=mime_type,
        size_bytes=len(content),
    )
    db.add(document)
    db.flush()

    _maybe_flag_duplicate_checksum(db, document)
    return document


def _maybe_flag_duplicate_checksum(db: Session, document: Document) -> None:
    """Raise a risk signal if the same checksum appears for another applicant."""
    stmt = select(Document).where(
        Document.tenant_id == document.tenant_id,
        Document.content_sha256 == document.content_sha256,
        Document.applicant_id != document.applicant_id,
        Document.id != document.id,
        Document.deleted_at.is_(None),
    )
    other = db.scalar(stmt)
    if other is None:
        return
    risk_service.add_signal(
        db,
        tenant_id=document.tenant_id,
        case_id=document.case_id,
        code=DUPLICATE_CHECKSUM_CODE,
        description="Identical document checksum used by a different applicant.",
        severity=RiskSeverity.high,
        weight=40,
        evidence={
            "content_sha256": document.content_sha256,
            "this_document_id": str(document.id),
            "other_document_id": str(other.id),
            "other_applicant_id": str(other.applicant_id),
        },
    )


def get_document(db: Session, tenant_id: uuid.UUID, document_id: uuid.UUID) -> Document:
    stmt = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id,
        Document.deleted_at.is_(None),
    )
    document = db.scalar(stmt)
    if document is None:
        raise NotFoundError("Document")
    return document


def list_documents(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> list[Document]:
    stmt = (
        select(Document)
        .where(
            Document.tenant_id == tenant_id,
            Document.case_id == case_id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def load_original_bytes(document: Document) -> bytes:
    if not document.storage_key:
        raise NotFoundError("Document content")
    return get_object(document.storage_key)


def load_redacted_bytes(document: Document) -> bytes:
    if not document.redacted_storage_key:
        raise NotFoundError("Redacted document preview")
    return get_object(document.redacted_storage_key)
