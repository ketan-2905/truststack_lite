"""Plain-data inputs/outputs for the pure risk calculators.

``CaseFacts`` is assembled from the database by the engine, but the calculators
depend only on this dataclass so they are pure and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import RiskSeverity


@dataclass
class CaseFacts:
    case_id: str
    applicant_consent: bool = True
    is_minor: bool = False
    guardian_consent: bool = False
    document_count: int = 0
    unsupported_document_count: int = 0
    # Verification step statuses present on the case (normalized strings).
    verification_statuses: list[str] = field(default_factory=list)
    # Count of recent cases for the same applicant identity (velocity).
    recent_case_count: int = 0
    # Pre-existing persisted signal codes (e.g. duplicate_artifact from MD05,
    # provider failures from MD06) so calculators don't double-count.
    existing_signal_codes: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class SignalSpec:
    code: str
    description: str
    severity: RiskSeverity
    weight: float
    evidence: dict = field(default_factory=dict)
