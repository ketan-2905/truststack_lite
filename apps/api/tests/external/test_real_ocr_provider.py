"""Gated real-OCR test.

Skipped unless RUN_EXTERNAL_TESTS=true. When enabled, it requires a real OCR
provider to be configured and FAILS LOUDLY (naming the env vars) otherwise — it
never silently passes without a live provider.
"""

from __future__ import annotations

import io
import os

import pytest
from PIL import Image, ImageDraw

RUN_EXTERNAL = os.environ.get("RUN_EXTERNAL_TESTS", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_EXTERNAL, reason="Set RUN_EXTERNAL_TESTS=true to run real OCR provider tests."
)


def _sample_image() -> bytes:
    img = Image.new("RGB", (400, 120), "white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "PAN ABCDE1234F", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_real_ocr_provider_extracts_text():
    from app.config import settings
    from app.ocr import get_ocr_provider

    # Fail loudly with the exact missing configuration rather than skipping.
    assert settings.ocr_configured, (
        "OCR provider is not configured. Set OCR_PROVIDER and the matching "
        "credentials (AWS_TEXTRACT_REGION + AWS creds, or "
        "GOOGLE_APPLICATION_CREDENTIALS) to run this external test."
    )

    provider = get_ocr_provider()
    result = provider.extract(_sample_image(), mime_type="image/png")
    assert result.provider
    assert result.full_text is not None
    assert isinstance(result.blocks, list)
