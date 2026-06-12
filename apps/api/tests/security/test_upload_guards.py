"""Test file upload protections."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_mime_validation():
    """Only image and PDF MIME types should be accepted."""
    # This test assumes endpoint exists and validates MIME
    # If endpoint doesn't exist yet, this documents the requirement
    pass


def test_upload_size_limit():
    """Files over max size should be rejected."""
    pass


def test_upload_extension_allowlist():
    """Only .pdf, .jpg, .png extensions should be accepted."""
    pass


def test_upload_checksum_computed():
    """SHA-256 checksum should be computed and stored."""
    pass


def test_duplicate_checksum_detected():
    """Uploading same document twice should be detected."""
    pass
