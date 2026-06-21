"""OCR provider interface and normalized result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class OcrBlock:
    """A recognized text block with a pixel-space bounding box.

    bbox is ``(x0, y0, x1, y1)`` in absolute pixel coordinates of the source
    image, which is what the redaction processor needs to draw over.
    """

    text: str
    bbox: tuple[float, float, float, float]
    confidence: float | None = None

    def as_dict(self) -> dict:
        return {"text": self.text, "bbox": list(self.bbox), "confidence": self.confidence}


@dataclass
class OcrResult:
    full_text: str
    blocks: list[OcrBlock] = field(default_factory=list)
    provider: str = ""
    width: int | None = None
    height: int | None = None

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "full_text": self.full_text,
            "width": self.width,
            "height": self.height,
            "blocks": [b.as_dict() for b in self.blocks],
        }


@runtime_checkable
class OcrProvider(Protocol):
    name: str

    def extract(self, image_bytes: bytes, *, mime_type: str | None = None) -> OcrResult:
        """Run OCR on the given image bytes and return a normalized result.

        Implementations call a real external OCR API. They must raise on
        authentication/credential errors rather than returning empty results.
        """
        ...
