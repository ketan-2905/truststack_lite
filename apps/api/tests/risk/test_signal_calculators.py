"""Pure signal calculator tests (no DB, fully deterministic)."""

from __future__ import annotations

from app.risk.calculators import (
    calc_minor_guardian_missing,
    calc_missing_consent,
    calc_unsupported_document,
    calc_velocity_anomaly,
    run_calculators,
)
from app.risk.facts import CaseFacts


def test_missing_consent_signal():
    assert calc_missing_consent(CaseFacts("c", applicant_consent=True)) == []
    sig = calc_missing_consent(CaseFacts("c", applicant_consent=False))
    assert len(sig) == 1 and sig[0].code == "missing_consent" and sig[0].weight == 50


def test_minor_guardian_signal():
    # Adult -> no signal.
    assert calc_minor_guardian_missing(CaseFacts("c", is_minor=False)) == []
    # Minor with guardian consent -> no signal.
    assert calc_minor_guardian_missing(
        CaseFacts("c", is_minor=True, guardian_consent=True)
    ) == []
    # Minor without guardian consent -> signal.
    sig = calc_minor_guardian_missing(CaseFacts("c", is_minor=True, guardian_consent=False))
    assert sig and sig[0].code == "minor_guardian_missing"


def test_unsupported_document_signal():
    assert calc_unsupported_document(CaseFacts("c", unsupported_document_count=0)) == []
    sig = calc_unsupported_document(CaseFacts("c", unsupported_document_count=2))
    assert sig and sig[0].code == "unsupported_document"


def test_velocity_signal_threshold():
    assert calc_velocity_anomaly(CaseFacts("c", recent_case_count=2)) == []
    sig = calc_velocity_anomaly(CaseFacts("c", recent_case_count=3))
    assert sig and sig[0].code == "velocity_anomaly"


def test_run_calculators_aggregates_deterministically():
    facts = CaseFacts(
        "c", applicant_consent=False, is_minor=True, guardian_consent=False,
        unsupported_document_count=1, recent_case_count=5,
    )
    codes = {s.code for s in run_calculators(facts)}
    assert codes == {
        "missing_consent",
        "minor_guardian_missing",
        "unsupported_document",
        "velocity_anomaly",
    }
    # Pure: same input -> identical output.
    assert run_calculators(facts) == run_calculators(facts)
