"""Pure decision-logic tests (no DB)."""

from __future__ import annotations

from app.enums import DecisionType
from app.risk.engine import decide


def _sig(code, weight, severity="medium"):
    return {"code": code, "weight": weight, "severity": severity, "description": code}


def test_clean_case_is_approved():
    result = decide([], dependency_blocked=False)
    assert result.decision == DecisionType.approved
    assert result.score == 0


def test_score_in_review_band_is_manual_review():
    result = decide([_sig("some_signal", 45)], dependency_blocked=False)
    assert result.decision == DecisionType.manual_review
    assert result.score == 45


def test_high_score_is_rejected():
    result = decide([_sig("a", 40), _sig("b", 35)], dependency_blocked=False)
    assert result.score == 75
    assert result.decision == DecisionType.rejected


def test_hard_reject_code_forces_rejection_regardless_of_score():
    result = decide([_sig("tamper_suspected", 5, "critical")], dependency_blocked=False)
    assert result.decision == DecisionType.rejected


def test_hard_review_code_forces_review():
    result = decide([_sig("duplicate_artifact", 5)], dependency_blocked=False)
    assert result.decision == DecisionType.manual_review


def test_dependency_blocked_overrides_everything():
    result = decide([_sig("tamper_suspected", 90, "critical")], dependency_blocked=True)
    assert result.decision == DecisionType.blocked_dependency


def test_duplicate_codes_collapse():
    result = decide(
        [_sig("dup", 40), _sig("dup", 40), _sig("dup", 30)], dependency_blocked=False
    )
    # Only counted once, with the max weight (40).
    assert result.score == 40
    assert len(result.reason_codes) == 1


def test_explanation_is_present_and_reproducible():
    signals = [_sig("missing_consent", 50, "high")]
    a = decide(signals, dependency_blocked=False)
    b = decide(signals, dependency_blocked=False)
    assert a.explanation == b.explanation
    assert a.explanation["policy_version"]
    assert a.explanation["reasons"][0]["code"] == "missing_consent"
