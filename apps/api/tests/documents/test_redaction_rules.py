"""Redaction processor unit tests (pure, no OCR provider needed).

These feed KNOWN OCR output to the redactor — this tests the redaction
algorithm, not OCR. Real OCR is exercised only by the gated external test.
"""

from __future__ import annotations

import io

from PIL import Image

from app.ocr.base import OcrBlock
from app.redaction import find_pii, redact_image, redact_text, text_has_pii


def test_find_pii_detects_indian_identifiers():
    labels = {label for label, _ in find_pii("PAN ABCDE1234F Aadhaar 1234 5678 9012 ph +919876543210")}
    assert {"pan", "aadhaar", "phone"} <= labels


def test_find_pii_ignores_plain_text():
    assert find_pii("just a normal name and address") == []
    assert not text_has_pii("hello world")


def test_redact_text_masks_pan():
    masked = redact_text("my pan is ABCDE1234F ok")
    assert "ABCDE1234F" not in masked
    assert "•" in masked


def test_redact_image_blacks_out_only_pii_blocks():
    img = Image.new("RGB", (300, 200), "white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    blocks = [
        OcrBlock(text="ABCDE1234F", bbox=(10, 10, 120, 40)),   # PAN -> redacted
        OcrBlock(text="John Smith", bbox=(10, 100, 120, 130)),  # not PII -> kept
    ]
    redacted_bytes, count = redact_image(buf.getvalue(), blocks)
    assert count == 1

    out = Image.open(io.BytesIO(redacted_bytes)).convert("RGB")
    assert out.getpixel((15, 15)) == (0, 0, 0)        # PAN region blacked out
    assert out.getpixel((15, 105)) == (255, 255, 255)  # name region untouched


def test_pipeline_without_ocr_marks_dependency_not_configured(
    make_tenant, make_applicant, make_case, db_session, monkeypatch
):
    """The OCR pipeline must fail loudly (no fake success) when unconfigured."""
    from app.config import settings
    from app.enums import DocumentStatus, DocumentType, VerificationStepStatus
    from app.models.document import Document
    from app.storage import put_object
    from app.tasks.documents import process_document_ocr

    monkeypatch.setattr(settings, "ocr_provider", None)  # deterministic: OCR off
    tenant = make_tenant(slug="redact-pipe")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)

    key = f"{tenant.id}/{case.id}/test/original/x.png"
    img = Image.new("RGB", (50, 50), "white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    put_object(key, buf.getvalue(), content_type="image/png")

    document = Document(
        tenant_id=tenant.id,
        case_id=case.id,
        applicant_id=applicant.id,
        doc_type=DocumentType.pan,
        status=DocumentStatus.uploaded,
        storage_key=key,
        mime_type="image/png",
        size_bytes=buf.getbuffer().nbytes,
    )
    db_session.add(document)
    db_session.commit()

    step = process_document_ocr(db_session, document)
    db_session.commit()

    assert step.status == VerificationStepStatus.dependency_not_configured
    assert document.status == DocumentStatus.failed
    assert "OCR_PROVIDER" in (step.failure_reason or "")
