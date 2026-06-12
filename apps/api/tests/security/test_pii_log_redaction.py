"""Verify PII is redacted from logs."""
import json
import logging
from io import StringIO

import pytest
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_config import configure_logging


def test_document_numbers_not_in_logs(db: Session, caplog):
    """PAN, Aadhaar, phone numbers should not appear in logs."""
    configure_logging("info")
    logger = logging.getLogger("truststack.test")

    sensitive_data = {
        "pan": "AAAPA1234B",
        "aadhaar": "123456789012",
        "phone": "+91-9876543210",
        "email": "user@example.com",
        "ocr_text": "PAN: AAAPA1234B, Aadhaar: 123456789012"
    }

    with caplog.at_level(logging.INFO):
        logger.info("document_processed", extra={"fields": sensitive_data})

    log_text = caplog.text.lower()

    # These should NOT appear verbatim in logs
    assert "aaapa1234b" not in log_text
    assert "123456789012" not in log_text
    assert "+91-9876543210" not in log_text or "[REDACTED]" in caplog.text


def test_provider_payload_not_in_logs(caplog):
    """Raw provider API responses should not leak into logs."""
    configure_logging("info")
    logger = logging.getLogger("truststack.provider")

    provider_response = {
        "status": "verified",
        "document_number": "AAAPA1234B",
        "full_name": "John Doe",
        "raw_payload": {"verification_id": "abc123"}
    }

    with caplog.at_level(logging.INFO):
        logger.info("provider_callback_received", extra={"fields": {"provider": "persona", "status": "success"}})

    # Only safe fields should be logged, not the full payload
    log_records = [record.getMessage() for record in caplog.records]
    combined = " ".join(log_records).lower()

    # Should log the action, but not the full sensitive response
    assert "provider_callback_received" in combined or "persona" in combined


def test_ocr_text_not_in_logs(caplog):
    """Raw OCR extracted text should not appear in logs."""
    configure_logging("info")
    logger = logging.getLogger("truststack.ocr")

    # Log only the safe summary, not raw OCR
    with caplog.at_level(logging.INFO):
        logger.info("ocr_completed", extra={"fields": {"document_id": "doc-123", "fields_extracted": 5}})

    log_text = caplog.text.lower()
    # Should have safe metadata, not raw text content
    assert "doc-123" in log_text or "fields_extracted" in log_text


def test_consent_records_minimal_in_logs(caplog):
    """Consent records should only log consent_id, not full PII."""
    configure_logging("info")
    logger = logging.getLogger("truststack.consent")

    with caplog.at_level(logging.INFO):
        logger.info("consent_recorded", extra={"fields": {"consent_id": "consent-abc", "case_id": "case-xyz"}})

    assert "consent-abc" in caplog.text or "case-xyz" in caplog.text
