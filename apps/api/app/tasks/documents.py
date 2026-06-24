"""Document OCR + redaction pipeline (worker task).

Real pipeline: download the stored image, run OCR via the configured live
provider, persist extraction, then redact PII regions into a derivative stored
back in object storage. If OCR is not configured, the document and its
verification step are marked accordingly (``dependency_not_configured``) — never
a fake OCR success.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.enums import (
    DocumentStatus,
    VerificationStepStatus,
    VerificationStepType,
)
from app.errors import DependencyNotConfiguredError
from app.hashing import sha256_hex
from app.logging_config import get_logger
from app.models.document import Document
from app.models.verification import VerificationStep
from app.ocr import get_ocr_provider
from app.ocr.base import OcrBlock
from app.redaction import redact_image, redact_text
from app.services import audit
from app.services import documents as document_service
from app.storage import put_object

logger = get_logger("truststack.tasks.documents")


def _now() -> datetime:
    return datetime.now(UTC)


def _get_or_create_ocr_step(db: Session, document: Document) -> VerificationStep:
    step = VerificationStep(
        tenant_id=document.tenant_id,
        case_id=document.case_id,
        step_type=VerificationStepType.document_ocr,
        status=VerificationStepStatus.running,
        provider=None,
        started_at=_now(),
    )
    db.add(step)
    db.flush()
    return step


def process_document_ocr(db: Session, document: Document) -> VerificationStep:
    """Run OCR + redaction for a document within the given session."""
    step = _get_or_create_ocr_step(db, document)
    document.status = DocumentStatus.processing
    db.flush()

    audit.record_event(
        db,
        tenant_id=document.tenant_id,
        actor_type="system",
        actor_id="worker",
        action="ocr.started",
        resource_type="document",
        resource_id=document.id,
        case_id=document.case_id,
        data={"document_id": str(document.id)},
    )

    try:
        provider = get_ocr_provider()
    except DependencyNotConfiguredError as exc:
        step.status = VerificationStepStatus.dependency_not_configured
        step.failure_reason = exc.detail["message"]
        step.completed_at = _now()
        document.status = DocumentStatus.failed
        db.flush()
        audit.record_event(
            db,
            tenant_id=document.tenant_id,
            actor_type="system",
            actor_id="worker",
            action="ocr.failed",
            resource_type="document",
            resource_id=document.id,
            case_id=document.case_id,
            data={"reason": "dependency_not_configured", "detail": exc.detail["message"]},
        )
        return step

    step.provider = provider.name
    try:
        content = document_service.load_original_bytes(document)
        result = provider.extract(content, mime_type=document.mime_type)
    except Exception as exc:  # noqa: BLE001 - record the real failure, don't crash worker
        step.status = VerificationStepStatus.failed
        step.failure_reason = f"{type(exc).__name__}: {exc}"
        step.completed_at = _now()
        document.status = DocumentStatus.failed
        db.flush()
        audit.record_event(
            db,
            tenant_id=document.tenant_id,
            actor_type="system",
            actor_id="worker",
            action="ocr.failed",
            resource_type="document",
            resource_id=document.id,
            case_id=document.case_id,
            data={"error": str(exc)},
        )
        logger.warning("ocr_failed", extra={"fields": {"document_id": str(document.id)}})
        return step

    # Persist extraction (raw text + bounding boxes).
    document.ocr_fields = result.as_dict()
    step.response_payload = {
        "provider": result.provider,
        "block_count": len(result.blocks),
        "full_text_sha256": sha256_hex(result.full_text),
        "redacted_text": redact_text(result.full_text),
    }
    step.status = VerificationStepStatus.succeeded
    step.completed_at = _now()
    db.flush()

    audit.record_event(
        db,
        tenant_id=document.tenant_id,
        actor_type="system",
        actor_id="worker",
        action="ocr.completed",
        resource_type="document",
        resource_id=document.id,
        case_id=document.case_id,
        data={"provider": result.provider, "blocks": len(result.blocks)},
    )

    _redact_document(db, document, content, result.blocks)
    return step


def _redact_document(
    db: Session, document: Document, content: bytes, blocks: list[OcrBlock]
) -> None:
    if document.mime_type not in document_service.IMAGE_MIME_TYPES:
        # Non-image (e.g. PDF) redaction requires rasterization; mark processed
        # without an image derivative rather than fake a redaction.
        document.status = DocumentStatus.processed
        db.flush()
        return

    redacted_bytes, count = redact_image(content, blocks)
    key = document_service.redacted_key(document)
    put_object(key, redacted_bytes, content_type="image/png")
    document.redacted_storage_key = key
    document.status = DocumentStatus.processed
    db.flush()

    audit.record_event(
        db,
        tenant_id=document.tenant_id,
        actor_type="system",
        actor_id="worker",
        action="redaction.completed",
        resource_type="document",
        resource_id=document.id,
        case_id=document.case_id,
        data={"redacted_regions": count, "redacted_key": key},
    )


def run_ocr_pipeline(document_id: str) -> str:
    """RQ entrypoint: process a document by id in its own session."""
    with SessionLocal() as db:
        document = db.get(Document, uuid.UUID(str(document_id)))
        if document is None:
            logger.warning("ocr_document_missing", extra={"fields": {"document_id": document_id}})
            return "missing"
        step = process_document_ocr(db, document)
        db.commit()
        return step.status.value
