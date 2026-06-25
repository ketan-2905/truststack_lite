"""md07 risk engine policy versioning

Revision ID: c3e25b8d1f02
Revises: b2d14a7c9e01
Create Date: 2026-06-28 00:30:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3e25b8d1f02"
down_revision: str | None = "b2d14a7c9e01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE decision_type ADD VALUE IF NOT EXISTS 'blocked_dependency'")

    op.add_column(
        "risk_signals",
        sa.Column("policy_version", sa.String(length=32), nullable=True),
    )
    op.create_index(
        op.f("ix_risk_signals_policy_version"), "risk_signals", ["policy_version"]
    )

    op.add_column(
        "risk_decisions",
        sa.Column("policy_version", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "risk_decisions",
        sa.Column("explanation", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        op.f("ix_risk_decisions_policy_version"), "risk_decisions", ["policy_version"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_risk_decisions_policy_version"), table_name="risk_decisions")
    op.drop_column("risk_decisions", "explanation")
    op.drop_column("risk_decisions", "policy_version")
    op.drop_index(op.f("ix_risk_signals_policy_version"), table_name="risk_signals")
    op.drop_column("risk_signals", "policy_version")
