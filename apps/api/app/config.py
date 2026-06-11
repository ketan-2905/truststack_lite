"""Application configuration loaded from environment variables.

No secrets are hard-coded. Every value is sourced from the environment so the
same image runs locally (MinIO) and in the cloud (real S3 / managed Postgres).
External provider credentials are intentionally optional: when they are absent
the system reports the dependency as ``not_configured`` and the endpoints that
need them fail loudly with ``424 Failed Dependency`` instead of faking success.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    service_name: str = Field(default="truststack-api", alias="SERVICE_NAME")

    # ── Auth / crypto ────────────────────────────────────────────────────────
    jwt_secret: str = Field(
        default="change-me-local-jwt-secret-please-rotate-0123456789",
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_minutes: int = Field(
        default=10080, alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+psycopg://truststack:truststack@postgres:5432/truststack",
        alias="DATABASE_URL",
    )
    test_database_url: str = Field(
        default="postgresql+psycopg://truststack:truststack@postgres:5432/truststack_test",
        alias="TEST_DATABASE_URL",
    )

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # ── Object storage (MinIO locally, S3 in cloud) ──────────────────────────
    s3_endpoint_url: str | None = Field(
        default="http://minio:9000", alias="S3_ENDPOINT_URL"
    )
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_access_key_id: str = Field(default="truststack", alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(
        default="truststack-secret", alias="S3_SECRET_ACCESS_KEY"
    )
    s3_bucket: str = Field(default="truststack-documents", alias="S3_BUCKET")
    s3_use_path_style: bool = Field(default=True, alias="S3_USE_PATH_STYLE")

    # ── External OCR provider (optional) ─────────────────────────────────────
    ocr_provider: str | None = Field(default=None, alias="OCR_PROVIDER")
    google_application_credentials: str | None = Field(
        default=None, alias="GOOGLE_APPLICATION_CREDENTIALS"
    )
    aws_textract_region: str | None = Field(default=None, alias="AWS_TEXTRACT_REGION")
    # Google Document AI (a distinct API from Vision).
    google_cloud_project_id: str | None = Field(
        default=None, alias="GOOGLE_CLOUD_PROJECT_ID"
    )
    google_document_ai_processor_id: str | None = Field(
        default=None, alias="GOOGLE_DOCUMENT_AI_PROCESSOR_ID"
    )
    google_document_ai_location: str = Field(
        default="us", alias="GOOGLE_DOCUMENT_AI_LOCATION"
    )
    google_document_ai_credentials: str | None = Field(
        default=None, alias="GOOGLE_DOCUMENT_AI_CREDENTIALS"
    )

    # ── External KYC / liveness provider (optional) ──────────────────────────
    kyc_provider: str | None = Field(default=None, alias="KYC_PROVIDER")
    kyc_api_key: str | None = Field(default=None, alias="KYC_API_KEY")
    kyc_api_url: str | None = Field(default=None, alias="KYC_API_URL")
    kyc_webhook_secret: str | None = Field(default=None, alias="KYC_WEBHOOK_SECRET")
    kyc_template_id: str | None = Field(default=None, alias="KYC_TEMPLATE_ID")

    # ── Webhooks ─────────────────────────────────────────────────────────────
    webhook_signing_secret: str = Field(
        default="change-me-local-webhook-secret", alias="WEBHOOK_SIGNING_SECRET"
    )
    webhook_max_attempts: int = Field(default=5, alias="WEBHOOK_MAX_ATTEMPTS")
    webhook_backoff_base_seconds: int = Field(
        default=2, alias="WEBHOOK_BACKOFF_BASE_SECONDS"
    )
    webhook_timeout_seconds: float = Field(default=10.0, alias="WEBHOOK_TIMEOUT_SECONDS")
    webhook_initial_dispatch_delay_seconds: int = Field(
        default=2, alias="WEBHOOK_INITIAL_DISPATCH_DELAY_SECONDS"
    )

    # ── Rate limiting ────────────────────────────────────────────────────────
    rate_limit_auth_per_minute: int = Field(
        default=10, alias="RATE_LIMIT_AUTH_PER_MINUTE"
    )
    rate_limit_apikey_per_minute: int = Field(
        default=60, alias="RATE_LIMIT_APIKEY_PER_MINUTE"
    )

    # ── Consent / privacy ────────────────────────────────────────────────────
    default_jurisdiction: str = Field(default="IN-DPDP", alias="DEFAULT_JURISDICTION")
    default_languages: str = Field(default="en,hi", alias="DEFAULT_LANGUAGES")

    # ── Seed data ────────────────────────────────────────────────────────────
    seed_tenant_name: str = Field(default="Acme Onboarding", alias="SEED_TENANT_NAME")
    seed_tenant_slug: str = Field(default="acme", alias="SEED_TENANT_SLUG")
    seed_admin_email: str = Field(
        default="admin@truststack.local", alias="SEED_ADMIN_EMAIL"
    )
    seed_admin_password: str = Field(
        default="change-me-local", alias="SEED_ADMIN_PASSWORD"
    )
    seed_analyst_email: str = Field(
        default="analyst@truststack.local", alias="SEED_ANALYST_EMAIL"
    )
    seed_analyst_password: str = Field(
        default="change-me-local", alias="SEED_ANALYST_PASSWORD"
    )

    @property
    def languages(self) -> list[str]:
        return [lang.strip() for lang in self.default_languages.split(",") if lang.strip()]

    @property
    def ocr_configured(self) -> bool:
        """OCR is configured only when a provider and its credential exist."""
        if not self.ocr_provider:
            return False
        provider = self.ocr_provider.lower()
        if provider in {"google", "google_vision", "gcv"}:
            return bool(self.google_application_credentials)
        if provider in {"aws", "textract", "aws_textract"}:
            return bool(self.aws_textract_region)
        if provider in {"google_document_ai", "document_ai", "docai"}:
            return bool(
                self.google_document_ai_processor_id
                and self.google_document_ai_credentials
            )
        return False

    @property
    def kyc_configured(self) -> bool:
        return bool(self.kyc_provider and self.kyc_api_key and self.kyc_api_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
