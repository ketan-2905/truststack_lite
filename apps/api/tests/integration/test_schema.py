"""Schema integrity tests against the real migrated database."""

from __future__ import annotations

from sqlalchemy import text

EXPECTED_TABLES = {
    "tenants",
    "users",
    "roles",
    "user_roles",
    "tenant_api_keys",
    "applicants",
    "onboarding_cases",
    "consent_notices",
    "consent_records",
    "documents",
    "verification_steps",
    "risk_signals",
    "risk_decisions",
    "review_tasks",
    "audit_events",
    "webhook_endpoints",
    "webhook_deliveries",
    "retention_requests",
}

EXPECTED_ENUMS = {
    "role_name",
    "case_state",
    "verification_step_type",
    "verification_step_status",
    "decision_type",
    "risk_severity",
    "review_status",
    "webhook_delivery_status",
    "document_type",
    "document_status",
    "consent_type",
    "retention_request_state",
}


def test_all_core_tables_exist(db_session):
    rows = db_session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    ).scalars().all()
    present = set(rows)
    missing = EXPECTED_TABLES - present
    assert not missing, f"missing tables: {missing}"


def test_all_enum_types_exist(db_session):
    rows = db_session.execute(
        text("SELECT typname FROM pg_type WHERE typtype = 'e'")
    ).scalars().all()
    present = set(rows)
    missing = EXPECTED_ENUMS - present
    assert not missing, f"missing enum types: {missing}"


def test_foreign_keys_are_indexed(db_session):
    # Every tenant_id column should be backed by an index (review-queue/tenant scans).
    rows = db_session.execute(
        text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    ).scalars().all()
    index_names = " ".join(rows)
    for table in ("applicants", "onboarding_cases", "audit_events", "documents"):
        assert f"ix_{table}_tenant_id" in index_names, f"{table}.tenant_id not indexed"


def test_migration_revision_recorded(db_session):
    version = db_session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version, "alembic_version should record the applied head revision"
