"""restore adaptive revision uniqueness for Stage 8E audit/concurrency

Revision ID: evolve22adaptive_audit
Revises: 0d74b80a4276
"""

from alembic import op
import sqlalchemy as sa

revision = "evolve22adaptive_audit"
down_revision = "0d74b80a4276"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_adaptive_plan_revision_user_version",
        "adaptive_plan_revisions",
        ["user_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_adaptive_plan_revision_user_version",
        table_name="adaptive_plan_revisions",
    )
