"""Risk recomputation worker task."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.logging_config import get_logger
from app.risk.engine import recompute_case_risk

logger = get_logger("truststack.tasks.risk")


def recompute_case_risk_task(tenant_id: str, case_id: str) -> str:
    """RQ entrypoint: recompute risk for a case in its own session."""
    with SessionLocal() as db:
        decision = recompute_case_risk(
            db, tenant_id=uuid.UUID(str(tenant_id)), case_id=uuid.UUID(str(case_id))
        )
        db.commit()
        logger.info(
            "risk_recomputed",
            extra={"fields": {"case_id": case_id, "decision": decision.decision.value}},
        )
        return decision.decision.value
