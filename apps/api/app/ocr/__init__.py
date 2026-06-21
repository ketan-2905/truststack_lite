"""Real OCR provider integrations.

Exactly one live provider is used, selected by ``OCR_PROVIDER``. There is no fake
provider: if no provider is configured (or its credentials are missing) the
registry raises ``DependencyNotConfiguredError`` (HTTP 424) naming the exact
environment variables required.
"""

from app.ocr.base import OcrBlock, OcrProvider, OcrResult
from app.ocr.registry import OCR_REQUIRED_ENV, get_ocr_provider

__all__ = [
    "OcrBlock",
    "OcrProvider",
    "OcrResult",
    "get_ocr_provider",
    "OCR_REQUIRED_ENV",
]
