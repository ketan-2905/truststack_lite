"""PII detection and image redaction.

Redaction is real server-side image processing: PII-bearing OCR blocks are
covered with opaque rectangles using their bounding boxes (not fake text-only
masking). The same PII detectors mask sensitive substrings in the stored text.
"""

from __future__ import annotations

import io
import re

from PIL import Image, ImageDraw

from app.ocr.base import OcrBlock

# Indian identity PII patterns.
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
# Indian mobile, optionally prefixed with +91/91. Digit lookarounds (not \b) so
# the leading + and surrounding digits are handled correctly.
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\-\s]?)?[6-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

_PATTERNS = [
    ("aadhaar", AADHAAR_RE),
    ("pan", PAN_RE),
    ("phone", PHONE_RE),
    ("email", EMAIL_RE),
]


def find_pii(text: str) -> list[tuple[str, str]]:
    """Return a list of ``(label, matched_text)`` for PII found in ``text``."""
    found: list[tuple[str, str]] = []
    for label, pattern in _PATTERNS:
        for match in pattern.finditer(text or ""):
            found.append((label, match.group(0)))
    return found


def text_has_pii(text: str) -> bool:
    return bool(find_pii(text))


def redact_text(text: str) -> str:
    """Mask PII substrings in text (keeps a short prefix for context)."""
    masked = text or ""
    for _label, pattern in _PATTERNS:
        masked = pattern.sub(lambda m: _mask(m.group(0)), masked)
    return masked


def _mask(value: str) -> str:
    keep = 2 if len(value) > 4 else 0
    return value[:keep] + "•" * (len(value) - keep)


def redact_image(image_bytes: bytes, blocks: list[OcrBlock]) -> tuple[bytes, int]:
    """Cover PII-bearing OCR blocks with opaque rectangles.

    Returns ``(redacted_png_bytes, redacted_block_count)``. Raises on a
    non-image input so callers handle unsupported formats explicitly.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    redacted = 0
    for block in blocks:
        if not text_has_pii(block.text):
            continue
        x0, y0, x1, y1 = block.bbox
        draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))
        redacted += 1

    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue(), redacted
