"""DB-backed risk recomputation: scenarios + idempotency."""

from __future__ import annotations

from sqlalchemy import text

from app.enums import (
    ConsentType,
    DecisionType,
    RiskSeverity,
    VerificationStepStatus,
    VerificationStepType,
)
from app.risk.engine import recompute_case_risk
from app.services import consent as consent_service
from app.services import risk as risk_service


def _grant_consent(db, tenant, case, applicant, notice, consent_type=ConsentType.applicant):
    consent_service.record_consent(
        db,
        tenant_id=tenant.id,
        case=case,
        applicant=applicant,
        notice=notice,
        granted=True,
        consent_type=consent_type,
        guardian_name="Guardian" if consent_type == ConsentType.guardian else None,
    )
    db.commit()


def _decision_count(db, case):
    return db.execute(
        text("SELECT count(*) FROM risk_decisions WHERE case_id = :c"), {"c": str(case.id)}
    ).scalar()


def test_clean_case_is_approved_and_idempotent(
    db_session, make_tenant, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="risk-1")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    _grant_consent(db_session, tenant, case, applicant, notice)

    d1 = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d1.decision == DecisionType.approved
    assert case.state.value == "approved"

    d2 = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d2.decision == DecisionType.approved
    assert _decision_count(db_session, case) == 1  # upsert, not duplicated


def test_missing_consent_goes_to_review_with_single_task(
    db_session, make_tenant, make_applicant, make_case
):
    tenant = make_tenant(slug="risk-2")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)

    d = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d.decision == DecisionType.manual_review

    recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()

    tasks = db_session.execute(
        text("SELECT count(*) FROM review_tasks WHERE case_id = :c"), {"c": str(case.id)}
    ).scalar()
    signals = db_session.execute(
        text("SELECT count(*) FROM risk_signals WHERE case_id = :c AND code='missing_consent'"),
        {"c": str(case.id)},
    ).scalar()
    assert tasks == 1  # not duplicated
    assert signals == 1  # not duplicated


def test_duplicate_artifact_triggers_review(
    db_session, make_tenant, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="risk-3")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    _grant_consent(db_session, tenant, case, applicant, notice)
    risk_service.add_signal(
        db_session, tenant_id=tenant.id, case_id=case.id, code="duplicate_artifact",
        description="dup", severity=RiskSeverity.high, weight=40,
    )
    db_session.commit()

    d = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d.decision == DecisionType.manual_review


def test_tamper_suspected_is_rejected(
    db_session, make_tenant, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="risk-4")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    _grant_consent(db_session, tenant, case, applicant, notice)
    risk_service.add_signal(
        db_session, tenant_id=tenant.id, case_id=case.id, code="tamper_suspected",
        description="tamper", severity=RiskSeverity.critical, weight=70,
    )
    db_session.commit()

    d = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d.decision == DecisionType.rejected
    assert case.state.value == "rejected"


def test_dependency_not_configured_blocks(
    db_session, make_tenant, make_applicant, make_case, make_consent_notice
):
    from app.models.verification import VerificationStep

    tenant = make_tenant(slug="risk-5")
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    _grant_consent(db_session, tenant, case, applicant, notice)
    db_session.add(
        VerificationStep(
            tenant_id=tenant.id,
            case_id=case.id,
            step_type=VerificationStepType.document_ocr,
            status=VerificationStepStatus.dependency_not_configured,
        )
    )
    db_session.commit()

    d = recompute_case_risk(db_session, tenant_id=tenant.id, case_id=case.id)
    db_session.commit()
    assert d.decision == DecisionType.blocked_dependency
