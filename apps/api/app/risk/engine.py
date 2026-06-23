"""Risk decision logic (pure ``decide``) and DB-backed ``recompute_case_risk``.

``decide`` is a pure function of the aggregated signals + policy, making the
decision fully reproducible and testable. ``recompute_case_risk`` is idempotent
per (case_id, policy_version): it dedupes signals by code and upserts a single
decision row.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import CaseState, DecisionType, RiskSeverity
from app.models.document import Document
from app.models.onboarding_case import OnboardingCase
from app.models.risk import RiskDecision
from app.models.verification import VerificationStep
from app.risk.calculators import run_calculators
from app.risk.facts import CaseFacts
from app.risk.policies import ACTIVE_POLICY
from app.risk.policies.v1 import Policy
from app.services import applicants as applicant_service
from app.services import audit
from app.services import cases as case_service
from app.services import consent as consent_service
from app.services import review as review_service
from app.services import risk as risk_service

_SEVERITY_ORDER = {
    RiskSeverity.low: 0,
    RiskSeverity.medium: 1,
    RiskSeverity.high: 2,
    RiskSeverity.critical: 3,
}


@dataclass
class DecisionResult:
    decision: DecisionType
    score: float
    severity: RiskSeverity
    reason_codes: list[dict] = field(default_factory=list)
    explanation: dict = field(default_factory=dict)


def _severity_from_score(score: float) -> RiskSeverity:
    if score >= 90:
        return RiskSeverity.critical
    if score >= 70:
        return RiskSeverity.high
    if score >= 40:
        return RiskSeverity.medium
    return RiskSeverity.low


def decide(
    signals: list[dict],
    *,
    dependency_blocked: bool,
    policy: Policy = ACTIVE_POLICY,
) -> DecisionResult:
    """Pure decision function.

    ``signals`` is a list of dicts with keys ``code``, ``severity`` (str), and
    ``weight`` (number). Identical codes are collapsed (max weight) so the result
    is independent of duplicate inputs.
    """
    by_code: dict[str, dict] = {}
    for s in signals:
        code = s["code"]
        if code not in by_code or float(s.get("weight", 0)) > float(by_code[code].get("weight", 0)):
            by_code[code] = s

    unique = list(by_code.values())
    score = min(100.0, sum(float(s.get("weight", 0)) for s in unique))
    codes = set(by_code.keys())

    score_severity = _severity_from_score(score)
    max_signal_severity = max(
        (RiskSeverity(s["severity"]) for s in unique if s.get("severity")),
        default=RiskSeverity.low,
        key=lambda sev: _SEVERITY_ORDER[sev],
    )
    severity = max(score_severity, max_signal_severity, key=lambda sev: _SEVERITY_ORDER[sev])

    if dependency_blocked:
        decision = DecisionType.blocked_dependency
    elif (codes & policy.hard_reject_codes) or score >= policy.reject_at:
        decision = DecisionType.rejected
    elif (codes & policy.hard_review_codes) or score >= policy.approve_below:
        decision = DecisionType.manual_review
    else:
        decision = DecisionType.approved

    reason_codes = sorted(
        (
            {
                "code": s["code"],
                "severity": s.get("severity"),
                "weight": float(s.get("weight", 0)),
                "description": s.get("description"),
            }
            for s in unique
        ),
        key=lambda r: (-r["weight"], r["code"]),
    )
    explanation = {
        "policy_version": policy.version,
        "decision": decision.value,
        "score": score,
        "severity": severity.value,
        "dependency_blocked": dependency_blocked,
        "thresholds": {"approve_below": policy.approve_below, "reject_at": policy.reject_at},
        "reasons": reason_codes,
    }
    return DecisionResult(
        decision=decision,
        score=score,
        severity=severity,
        reason_codes=reason_codes,
        explanation=explanation,
    )


# ── DB-backed recomputation ──────────────────────────────────────────────────
def _build_facts(db: Session, case: OnboardingCase, applicant) -> CaseFacts:
    docs = list(
        db.scalars(
            select(Document).where(
                Document.case_id == case.id, Document.deleted_at.is_(None)
            )
        ).all()
    )
    steps = list(
        db.scalars(select(VerificationStep).where(VerificationStep.case_id == case.id)).all()
    )
    case_count = len(
        list(
            db.scalars(
                select(OnboardingCase.id).where(
                    OnboardingCase.applicant_id == case.applicant_id
                )
            ).all()
        )
    )
    existing = {s.code for s in risk_service.list_signals(db, case.tenant_id, case.id)}

    return CaseFacts(
        case_id=str(case.id),
        applicant_consent=consent_service.applicant_consent_granted(db, case.id),
        is_minor=consent_service.is_minor(applicant),
        guardian_consent=consent_service.guardian_consent_granted(db, case.id),
        document_count=len(docs),
        unsupported_document_count=sum(
            1 for d in docs if d.mime_type not in {"image/png", "image/jpeg", "application/pdf"}
        ),
        verification_statuses=[s.status.value for s in steps],
        recent_case_count=case_count,
        existing_signal_codes=existing,
    )


def recompute_case_risk(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    decided_by: str = "system",
    decided_by_user_id: uuid.UUID | None = None,
) -> RiskDecision:
    policy = ACTIVE_POLICY
    case = case_service.get_case(db, tenant_id, case_id)
    applicant = applicant_service.get_applicant(db, tenant_id, case.applicant_id)

    facts = _build_facts(db, case, applicant)

    # Persist fact-derived signals (dedup by code so recompute is idempotent).
    for spec in run_calculators(facts):
        signal = risk_service.add_signal(
            db,
            tenant_id=tenant_id,
            case_id=case.id,
            code=spec.code,
            description=spec.description,
            severity=spec.severity,
            weight=spec.weight,
            evidence=spec.evidence,
            dedupe=True,
        )
        if signal is not None and signal.policy_version is None:
            signal.policy_version = policy.version
    db.flush()

    all_signals = risk_service.list_signals(db, tenant_id, case.id)
    signal_dicts = [
        {
            "code": s.code,
            "severity": s.severity.value,
            "weight": float(s.weight),
            "description": s.description,
        }
        for s in all_signals
    ]
    dependency_blocked = any(
        status in policy.dependency_blocked_statuses for status in facts.verification_statuses
    )

    result = decide(signal_dicts, dependency_blocked=dependency_blocked, policy=policy)

    # Upsert one decision per (case, policy_version).
    decision = db.scalar(
        select(RiskDecision).where(
            RiskDecision.case_id == case.id,
            RiskDecision.policy_version == policy.version,
        )
    )
    if decision is None:
        decision = RiskDecision(
            tenant_id=tenant_id,
            case_id=case.id,
            policy_version=policy.version,
        )
        db.add(decision)
    decision.decision = result.decision
    decision.score = result.score
    decision.severity = result.severity
    decision.reason_codes = result.reason_codes
    decision.explanation = result.explanation
    decision.decided_by = decided_by
    decision.decided_by_user_id = decided_by_user_id
    db.flush()

    # Reflect on the case.
    case.risk_score = result.score
    case.risk_severity = result.severity
    _apply_case_state(case, result.decision)

    if result.decision == DecisionType.manual_review:
        review_service.ensure_open_review_task(
            db, tenant_id=tenant_id, case_id=case.id, priority=_priority(result.severity)
        )

    db.flush()
    audit.record_event(
        db,
        tenant_id=tenant_id,
        actor_type="system" if decided_by == "system" else "user",
        actor_id=str(decided_by_user_id) if decided_by_user_id else "risk_engine",
        action="risk.decided",
        resource_type="risk_decision",
        resource_id=decision.id,
        case_id=case.id,
        data={
            "decision": result.decision.value,
            "score": result.score,
            "policy_version": policy.version,
        },
    )
    from app.services import events as event_service

    event_service.emit_event(
        db,
        tenant_id=tenant_id,
        event_type=event_service.EVENT_RISK_DECIDED,
        payload={
            "case_id": str(case.id),
            "decision": result.decision.value,
            "score": result.score,
            "severity": result.severity.value,
            "policy_version": policy.version,
        },
        case_id=case.id,
    )
    return decision


def _apply_case_state(case: OnboardingCase, decision: DecisionType) -> None:
    mapping = {
        DecisionType.approved: CaseState.approved,
        DecisionType.rejected: CaseState.rejected,
        DecisionType.manual_review: CaseState.in_review,
    }
    if decision in mapping:
        case.state = mapping[decision]
    # blocked_dependency leaves the current state so the dashboard shows it
    # blocked rather than resolved.


def _priority(severity: RiskSeverity) -> int:
    return {RiskSeverity.low: 1, RiskSeverity.medium: 2, RiskSeverity.high: 3, RiskSeverity.critical: 4}[
        severity
    ]


def latest_decision(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> RiskDecision | None:
    return db.scalar(
        select(RiskDecision)
        .where(RiskDecision.tenant_id == tenant_id, RiskDecision.case_id == case_id)
        .order_by(RiskDecision.created_at.desc())
    )
