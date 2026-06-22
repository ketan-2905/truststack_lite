"""Verification provider selection. Fails loudly when none is configured."""

from __future__ import annotations

from app.config import settings
from app.errors import ProviderNotConfiguredError
from app.verification.base import VerificationProvider

PROVIDER_REQUIRED_ENV = ["KYC_PROVIDER", "KYC_API_URL", "KYC_API_KEY"]

_SUPPORTED = {"persona"}


def get_verification_provider() -> VerificationProvider:
    if not (settings.kyc_provider and settings.kyc_api_url and settings.kyc_api_key):
        raise ProviderNotConfiguredError(PROVIDER_REQUIRED_ENV)

    provider = settings.kyc_provider.strip().lower()
    if provider == "persona":
        from app.verification.persona import PersonaProvider

        return PersonaProvider(
            api_url=settings.kyc_api_url,
            api_key=settings.kyc_api_key,
            webhook_secret=settings.kyc_webhook_secret,
            template_id=settings.kyc_template_id,
        )

    raise ProviderNotConfiguredError(
        [f"KYC_PROVIDER must be one of: {sorted(_SUPPORTED)}", *PROVIDER_REQUIRED_ENV]
    )
