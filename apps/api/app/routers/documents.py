"""Document upload, listing, and safe (redacted) preview endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import ALL_TENANT_ROLES, WRITE_ROLES, Principal, require_roles
from app.enums import DocumentStatus, DocumentType, RoleName
from app.errors import DependencyNotConfiguredError
from app.ocr import OCR_REQUIRED_ENV
from app.queue import QUEUE_VERIFICATION, enqueue
from app.schemas.document import DocumentOut
from app.services import applicants as applicant_service
from app.services import audit
from app.services import cases as case_service
from app.services import documents as document_service
from app.tasks.documents import process_document_ocr, run_ocr_pipeline

WRITER = require_roles(*WRITE_ROLES)
READER = require_roles(*ALL_TENANT_ROLES)
ORIGINAL_VIEWER = require_roles(RoleName.tenant_admin)

router = APIRouter(tags=["documents"])


@router.post(
    "/v1/onboarding-cases/{case_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    doc_type: DocumentType = Form(...),
    process: bool = Query(default=True),
    principal: Principal = Depends(WRITER),
    db: Session = Depends(get_db),
) -> DocumentOut:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    applicant = applicant_service.get_applicant(db, principal.tenant_id, case.applicant_id)

    content = file.file.read()
    document = document_service.create_document(
        db,
        tenant_id=principal.tenant_id,
        case=case,
        applicant=applicant,
        doc_type=doc_type,
        filename=file.filename or "upload",
        content=content,
        mime_type=file.content_type or "application/octet-stream",
    )
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="document.uploaded",
        resource_type="document",
        resource_id=document.id,
        case_id=case.id,
        request=principal.request,
        data={"doc_type": doc_type.value, "sha256": document.content_sha256},
    )

    if not process:
        return DocumentOut.from_model(document)

    if settings.ocr_configured:
        document.status = DocumentStatus.processing
        # Commit before enqueuing so the worker's separate session sees the row.
        db.commit()
        db.refresh(document)
        enqueue(run_ocr_pipeline, str(document.id), queue=QUEUE_VERIFICATION)
        return DocumentOut.from_model(document)

    # OCR not configured: record the dependency failure on the document/step,
    # commit it, then fail loudly with 424 (Flow C — no fake OCR success).
    process_document_ocr(db, document)
    db.commit()
    raise DependencyNotConfiguredError(
        "ocr",
        ["OCR_PROVIDER", *OCR_REQUIRED_ENV.get("aws_textract", []), "GOOGLE_APPLICATION_CREDENTIALS"],
    )


@router.get(
    "/v1/onboarding-cases/{case_id}/documents",
    response_model=list[DocumentOut],
)
def list_documents(
    case_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    case = case_service.get_case(db, principal.tenant_id, case_id)
    docs = document_service.list_documents(db, principal.tenant_id, case.id)
    return [DocumentOut.from_model(d) for d in docs]


@router.get("/v1/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = document_service.get_document(db, principal.tenant_id, document_id)
    return DocumentOut.from_model(document)


@router.get("/v1/documents/{document_id}/preview")
def preview_document(
    document_id: uuid.UUID,
    principal: Principal = Depends(READER),
    db: Session = Depends(get_db),
) -> Response:
    """Serve the REDACTED derivative only. Never exposes the raw document."""
    document = document_service.get_document(db, principal.tenant_id, document_id)
    data = document_service.load_redacted_bytes(document)
    return Response(content=data, media_type="image/png")


@router.get("/v1/documents/{document_id}/original")
def download_original(
    document_id: uuid.UUID,
    principal: Principal = Depends(ORIGINAL_VIEWER),
    db: Session = Depends(get_db),
) -> Response:
    """Serve the unredacted original. Restricted to tenant_admin and audited."""
    document = document_service.get_document(db, principal.tenant_id, document_id)
    data = document_service.load_original_bytes(document)
    audit.record_event(
        db,
        tenant_id=principal.tenant_id,
        actor_type=principal.actor_type,
        actor_id=principal.actor_id,
        action="document.original_accessed",
        resource_type="document",
        resource_id=document.id,
        case_id=document.case_id,
        request=principal.request,
    )
    return Response(
        content=data, media_type=document.mime_type or "application/octet-stream"
    )
