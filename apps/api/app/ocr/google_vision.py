"""Google Cloud Vision OCR provider (real).

The ``google-cloud-vision`` client is imported lazily so the default image stays
lean. To use this provider, install ``google-cloud-vision`` and set
``GOOGLE_APPLICATION_CREDENTIALS`` to a service-account JSON path.
"""

from __future__ import annotations

import io

from PIL import Image


class GoogleVisionProvider:
    name = "google_vision"

    def __init__(self) -> None:
        try:
            from google.cloud import vision  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional lib
            raise RuntimeError(
                "google-cloud-vision is not installed. Install it to use "
                "OCR_PROVIDER=google_vision."
            ) from exc
        self._vision = vision
        self._client = vision.ImageAnnotatorClient()

    def extract(self, image_bytes: bytes, *, mime_type: str | None = None):
        from app.ocr.base import OcrBlock, OcrResult

        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size

        image = self._vision.Image(content=image_bytes)
        response = self._client.document_text_detection(image=image)
        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")

        blocks: list[OcrBlock] = []
        annotations = response.text_annotations
        full_text = annotations[0].description if annotations else ""
        # Skip index 0 (the full-page annotation); the rest are words.
        for ann in annotations[1:]:
            verts = ann.bounding_poly.vertices
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            blocks.append(
                OcrBlock(text=ann.description, bbox=(min(xs), min(ys), max(xs), max(ys)))
            )

        return OcrResult(
            full_text=full_text,
            blocks=blocks,
            provider=self.name,
            width=width,
            height=height,
        )
