"""Pure risk signal calculators.

Each function takes ``CaseFacts`` and returns zero or more ``SignalSpec``. They
are deterministic and side-effect free. Signals produced elsewhere
(``duplicate_artifact`` in MD 05, provider failures in MD 06) are already
persisted and are merged by the engine — the calculators here cover the
fact-derived categories.
"""

from __future__ import annotations

from collections.abc import Callable

from app.enums import RiskSeverity
from app.risk.facts import CaseFacts, SignalSpec


def calc_missing_consent(facts: CaseFacts) -> list[SignalSpec]:
    if facts.applicant_consent:
        return []
    return [
        SignalSpec(
            code="missing_consent",
            description="Required applicant consent is not present.",
            severity=RiskSeverity.high,
            weight=50,
            evidence={"applicant_consent": False},
        )
    ]


def calc_minor_guardian_missing(facts: CaseFacts) -> list[SignalSpec]:
    if not facts.is_minor or facts.guardian_consent:
        return []
    return [
        SignalSpec(
            code="minor_guardian_missing",
            description="Applicant is a minor and guardian consent is missing.",
            severity=RiskSeverity.critical,
            weight=60,
            evidence={"is_minor": True, "guardian_consent": False},
        )
    ]


def calc_unsupported_document(facts: CaseFacts) -> list[SignalSpec]:
    if facts.unsupported_document_count <= 0:
        return []
    return [
        SignalSpec(
            code="unsupported_document",
            description="One or more documents have an unsupported format.",
            severity=RiskSeverity.medium,
            weight=25,
            evidence={"count": facts.unsupported_document_count},
        )
    ]


def calc_velocity_anomaly(facts: CaseFacts) -> list[SignalSpec]:
    if facts.recent_case_count < 3:
        return []
    return [
        SignalSpec(
            code="velocity_anomaly",
            description="Unusually high number of recent cases for this applicant.",
            severity=RiskSeverity.high,
            weight=40,
            evidence={"recent_case_count": facts.recent_case_count},
        )
    ]


CALCULATORS: list[Callable[[CaseFacts], list[SignalSpec]]] = [
    calc_missing_consent,
    calc_minor_guardian_missing,
    calc_unsupported_document,
    calc_velocity_anomaly,
]


def run_calculators(facts: CaseFacts) -> list[SignalSpec]:
    signals: list[SignalSpec] = []
    for calc in CALCULATORS:
        signals.extend(calc(facts))
    return signals
