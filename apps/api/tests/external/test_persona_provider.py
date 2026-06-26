"""Gated real Persona provider test.

Skipped unless RUN_EXTERNAL_TESTS=true. When enabled it requires real Persona
credentials and FAILS LOUDLY (naming env vars) otherwise — it never passes
without a live provider.
"""

from __future__ import annotations

import os

import pytest

RUN_EXTERNAL = os.environ.get("RUN_EXTERNAL_TESTS", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_EXTERNAL, reason="Set RUN_EXTERNAL_TESTS=true to run real provider tests."
)


def test_real_provider_creates_session():
    from app.config import settings
    from app.verification import get_verification_provider

    assert settings.kyc_provider and settings.kyc_api_url and settings.kyc_api_key, (
        "Verification provider is not configured. Set KYC_PROVIDER, KYC_API_URL, "
        "and KYC_API_KEY (and KYC_TEMPLATE_ID) to run this external test."
    )
    provider = get_verification_provider()
    session = provider.create_session(reference="external-test")
    assert session.provider_ref
    assert session.status is not None
