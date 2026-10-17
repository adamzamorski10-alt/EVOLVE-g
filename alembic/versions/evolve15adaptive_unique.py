"""enforce one adaptive revision version per user

Revision ID: evolve15adaptiveunique
Revises: evolve14resultsource
"""

from alembic import op


revision = "evolve15adaptiveunique"
down_revision = "evolve14resultsource"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX uq_adaptive_plan_revision_user_version "
        "ON adaptive_plan_revisions(user_id, version)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_adaptive_plan_revision_user_version")
