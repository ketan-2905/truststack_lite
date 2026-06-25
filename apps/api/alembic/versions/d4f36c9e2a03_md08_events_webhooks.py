"""md08 domain events, idempotency keys, webhook delivery attempts

Revision ID: d4f36c9e2a03
Revises: c3e25b8d1f02
Create Date: 2026-06-28 01:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4f36c9e2a03"
down_revision: str | None = "c3e25b8d1f02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("dispatched", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["onboarding_cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_domain_events_tenant_id"), "domain_events", ["tenant_id"])
    op.create_index(op.f("ix_domain_events_case_id"), "domain_events", ["case_id"])
    op.create_index(op.f("ix_domain_events_event_type"), "domain_events", ["event_type"])
    op.create_index(op.f("ix_domain_events_dispatched"), "domain_events", ["dispatched"])
    op.create_index(op.f("ix_domain_events_created_at"), "domain_events", ["created_at"])

    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_idempotency_tenant_key"),
    )
    op.create_index(op.f("ix_idempotency_keys_tenant_id"), "idempotency_keys", ["tenant_id"])
    op.create_index(op.f("ix_idempotency_keys_created_at"), "idempotency_keys", ["created_at"])

    op.create_table(
        "webhook_delivery_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("delivery_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body_hash", sa.String(length=64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["delivery_id"], ["webhook_deliveries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_webhook_delivery_attempts_delivery_id"),
        "webhook_delivery_attempts",
        ["delivery_id"],
    )
    op.create_index(
        op.f("ix_webhook_delivery_attempts_created_at"),
        "webhook_delivery_attempts",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("webhook_delivery_attempts")
    op.drop_table("idempotency_keys")
    op.drop_table("domain_events")
