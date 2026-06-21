"""Google Cloud Document AI OCR provider (real).

Uses the ``google-cloud-documentai`` client against a configured processor. The
processor path is ``projects/{project}/locations/{location}/processors/{id}``.
Credentials come from a service-account JSON file. Bounding boxes (normalized
vertices) are converted to absolute pixels for the redaction processor.
"""

from __future__ import annotations

import io
import json

from PIL import Image


class GoogleDocumentAiProvider:
    name = "google_document_ai"

    def __init__(
        self,
        *,
        project_id: str | None,
        processor_id: str,
        location: str,
        credentials_path: str,
    ) -> None:
        try:
            from google.api_core.client_options import ClientOptions
            from google.cloud import documentai  # type: ignore
            from google.oauth2 import service_account  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "google-cloud-documentai is not installed. Install it to use "
                "OCR_PROVIDER=google_document_ai."
            ) from exc

        self._documentai = documentai
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        # Fall back to the project in the credentials file when not set explicitly.
        if not project_id:
            with open(credentials_path) as fh:
                project_id = json.load(fh).get("project_id")
        self._project_id = project_id
        self._location = location
        self._processor_id = processor_id

        endpoint = f"{location}-documentai.googleapis.com"
        self._client = documentai.DocumentProcessorServiceClient(
            credentials=credentials,
            client_options=ClientOptions(api_endpoint=endpoint),
        )
        self._name = self._client.processor_path(project_id, location, processor_id)

    def extract(self, image_bytes: bytes, *, mime_type: str | None = None):
        from app.ocr.base import OcrBlock, OcrResult

        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size

        documentai = self._documentai
        raw_document = documentai.RawDocument(
            content=image_bytes, mime_type=mime_type or "image/png"
        )
        request = documentai.ProcessRequest(name=self._name, raw_document=raw_document)
        result = self._client.process_document(request=request)
        document = result.document
        text = document.text or ""

        blocks: list[OcrBlock] = []
        for page in document.pages:
            # Prefer line-level layout (better PII coverage); fall back to tokens.
            elements = list(page.lines) or list(page.tokens)
            for element in elements:
                layout = element.layout
                segment_text = _text_from_layout(layout, text)
                bbox = _bbox_from_layout(layout, width, height)
                if segment_text and bbox is not None:
                    blocks.append(OcrBlock(text=segment_text, bbox=bbox, confidence=layout.confidence))

        return OcrResult(
            full_text=text,
            blocks=blocks,
            provider=self.name,
            width=width,
            height=height,
        )


def _text_from_layout(layout, full_text: str) -> str:
    anchor = getattr(layout, "text_anchor", None)
    if anchor is None or not anchor.text_segments:
        return ""
    parts = []
    for segment in anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end = int(segment.end_index)
        parts.append(full_text[start:end])
    return "".join(parts).strip()


def _bbox_from_layout(layout, width: int, height: int):
    poly = getattr(layout, "bounding_poly", None)
    if poly is None:
        return None
    verts = list(poly.normalized_vertices) or list(poly.vertices)
    if not verts:
        return None
    normalized = bool(poly.normalized_vertices)
    xs = [(v.x * width) if normalized else v.x for v in verts]
    ys = [(v.y * height) if normalized else v.y for v in verts]
    return (min(xs), min(ys), max(xs), max(ys))
