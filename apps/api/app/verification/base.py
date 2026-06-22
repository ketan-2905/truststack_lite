"""Verification provider interface and normalized result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.enums import VerificationStepStatus


@dataclass
class ProviderSession:
    """Normalized provider session/inquiry result."""

    provider_ref: str
    status: VerificationStepStatus
    raw: dict = field(default_factory=dict)


@dataclass
class ParsedCallback:
    """Normalized provider webhook/callback."""

    provider_ref: str
    status: VerificationStepStatus
    event_type: str
    raw: dict = field(default_factory=dict)
    # Risk reason codes derived from a failing/needs-review outcome.
    risk_codes: list[str] = field(default_factory=list)


@runtime_checkable
class VerificationProvider(Protocol):
    name: str

    def create_session(self, *, reference: str, attributes: dict | None = None) -> ProviderSession:
        """Create a verification session/inquiry. Real network call."""
        ...

    def submit_document(self, *, provider_ref: str, document_bytes: bytes, doc_type: str) -> ProviderSession:
        ...

    def submit_selfie(self, *, provider_ref: str, selfie_bytes: bytes) -> ProviderSession:
        ...

    def get_status(self, *, provider_ref: str) -> ProviderSession:
        ...

    def cancel_session(self, *, provider_ref: str) -> ProviderSession:
        ...

    def verify_callback_signature(self, *, payload: bytes, signature_header: str | None) -> bool:
        ...

    def parse_callback(self, *, payload: bytes) -> ParsedCallback:
        ...
