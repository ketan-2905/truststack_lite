"""md06 verification traceability and normalized states

Revision ID: b2d14a7c9e01
Revises: f5c99ffbd630
Create Date: 2026-06-28 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d14a7c9e01"
down_revision: str | None = "f5c99ffbd630"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Normalized provider outcome states (PG 12+ allows ADD VALUE in a tx as long
    # as the new value is not used within the same transaction).
    op.execute("ALTER TYPE verification_step_status ADD VALUE IF NOT EXISTS 'needs_review'")
    op.execute("ALTER TYPE verification_step_status ADD VALUE IF NOT EXISTS 'provider_error'")

    # Provider traceability columns.
    op.add_column(
        "verification_steps",
        sa.Column("provider_ref", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "verification_steps",
        sa.Column("response_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_verification_steps_provider_ref"),
        "verification_steps",
        ["provider_ref"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_verification_steps_provider_ref"), table_name="verification_steps"
    )
    op.drop_column("verification_steps", "response_hash")
    op.drop_column("verification_steps", "provider_ref")
    # Note: PostgreSQL cannot easily DROP an enum value; the added values remain.
