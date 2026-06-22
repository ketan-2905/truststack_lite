"""Real verification provider adapters (KYC / liveness / document checks).

Vendor-agnostic boundary: exactly one live provider is selected via
``KYC_PROVIDER`` and configured with ``KYC_API_URL`` + ``KYC_API_KEY``. If no
provider is configured, the registry raises ``ProviderNotConfiguredError`` (HTTP
424, ``missing_provider_config``). No fake provider ever marks a verification as
passed.
"""

from app.verification.base import (
    ParsedCallback,
    ProviderSession,
    VerificationProvider,
)
from app.verification.registry import get_verification_provider

__all__ = [
    "VerificationProvider",
    "ProviderSession",
    "ParsedCallback",
    "get_verification_provider",
]
