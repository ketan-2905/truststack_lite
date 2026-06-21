"""AWS Textract OCR provider (real).

Uses boto3 (already a dependency). Textract returns geometry normalized to
[0, 1]; we convert to absolute pixels using the source image dimensions so the
redaction processor can draw over PII regions.
"""

from __future__ import annotations

import io

import boto3
from PIL import Image


class AwsTextractProvider:
    name = "aws_textract"

    def __init__(self, region: str) -> None:
        # Credentials come from the standard AWS chain (env/instance role). A
        # missing/invalid credential raises at call time — never a fake success.
        self._client = boto3.client("textract", region_name=region)

    def extract(self, image_bytes: bytes, *, mime_type: str | None = None):
        from app.ocr.base import OcrBlock, OcrResult

        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size

        response = self._client.detect_document_text(Document={"Bytes": image_bytes})

        blocks: list[OcrBlock] = []
        lines: list[str] = []
        for item in response.get("Blocks", []):
            if item.get("BlockType") not in {"LINE", "WORD"}:
                continue
            text = item.get("Text", "")
            box = item.get("Geometry", {}).get("BoundingBox")
            if not text or box is None:
                continue
            x0 = box["Left"] * width
            y0 = box["Top"] * height
            x1 = x0 + box["Width"] * width
            y1 = y0 + box["Height"] * height
            if item["BlockType"] == "LINE":
                lines.append(text)
            blocks.append(
                OcrBlock(text=text, bbox=(x0, y0, x1, y1), confidence=item.get("Confidence"))
            )

        return OcrResult(
            full_text="\n".join(lines),
            blocks=blocks,
            provider=self.name,
            width=width,
            height=height,
        )
