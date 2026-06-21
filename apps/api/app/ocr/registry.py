"""OCR provider selection. Fails loudly when no live provider is configured."""

from __future__ import annotations

from app.config import settings
from app.errors import DependencyNotConfiguredError
from app.ocr.base import OcrProvider

# Documented required env per provider (surfaced in the 424 error).
OCR_REQUIRED_ENV = {
    "aws_textract": ["AWS_TEXTRACT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "google_vision": ["GOOGLE_APPLICATION_CREDENTIALS"],
    "google_document_ai": [
        "GOOGLE_DOCUMENT_AI_PROCESSOR_ID",
        "GOOGLE_DOCUMENT_AI_CREDENTIALS",
        "GOOGLE_DOCUMENT_AI_LOCATION",
        "GOOGLE_CLOUD_PROJECT_ID (optional; inferred from credentials)",
    ],
}

_AWS_ALIASES = {"aws_textract", "textract", "aws"}
_GOOGLE_ALIASES = {"google_vision", "google", "gcv"}
_DOCAI_ALIASES = {"google_document_ai", "document_ai", "docai"}


def get_ocr_provider() -> OcrProvider:
    """Return the configured live OCR provider, or raise 424 with the exact
    environment variables required."""
    provider = (settings.ocr_provider or "").lower()
    if not provider:
        raise DependencyNotConfiguredError(
            "ocr",
            ["OCR_PROVIDER (e.g. aws_textract or google_vision) + provider credentials"],
        )

    if provider in _AWS_ALIASES:
        if not settings.aws_textract_region:
            raise DependencyNotConfiguredError("ocr:aws_textract", OCR_REQUIRED_ENV["aws_textract"])
        from app.ocr.textract import AwsTextractProvider

        return AwsTextractProvider(region=settings.aws_textract_region)

    if provider in _GOOGLE_ALIASES:
        if not settings.google_application_credentials:
            raise DependencyNotConfiguredError(
                "ocr:google_vision", OCR_REQUIRED_ENV["google_vision"]
            )
        from app.ocr.google_vision import GoogleVisionProvider

        return GoogleVisionProvider()

    if provider in _DOCAI_ALIASES:
        if not (
            settings.google_document_ai_processor_id
            and settings.google_document_ai_credentials
        ):
            raise DependencyNotConfiguredError(
                "ocr:google_document_ai", OCR_REQUIRED_ENV["google_document_ai"]
            )
        from app.ocr.google_document_ai import GoogleDocumentAiProvider

        return GoogleDocumentAiProvider(
            project_id=settings.google_cloud_project_id,
            processor_id=settings.google_document_ai_processor_id,
            location=settings.google_document_ai_location,
            credentials_path=settings.google_document_ai_credentials,
        )

    raise DependencyNotConfiguredError(
        f"ocr:{provider}",
        ["OCR_PROVIDER must be one of: aws_textract, google_vision, google_document_ai"],
    )
