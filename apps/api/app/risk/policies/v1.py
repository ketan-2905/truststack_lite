"""Risk policy v1 (config as code).

Thresholds (default): approve < 40, manual review 40-69, reject >= 70. Some
signal codes are hard rules that force a decision regardless of score.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    version: str
    approve_below: float
    reject_at: float
    # Codes that force manual review regardless of score.
    hard_review_codes: frozenset[str] = field(default_factory=frozenset)
    # Codes that force rejection regardless of score.
    hard_reject_codes: frozenset[str] = field(default_factory=frozenset)
    # Verification step statuses that mean the case cannot be decided yet.
    dependency_blocked_statuses: frozenset[str] = field(default_factory=frozenset)


POLICY = Policy(
    version="2026.01",
    approve_below=40,
    reject_at=70,
    hard_review_codes=frozenset(
        {
            "missing_consent",
            "minor_guardian_missing",
            "duplicate_artifact",
            "provider_needs_review",
            "velocity_anomaly",
        }
    ),
    hard_reject_codes=frozenset({"tamper_suspected"}),
    dependency_blocked_statuses=frozenset({"dependency_not_configured"}),
)
