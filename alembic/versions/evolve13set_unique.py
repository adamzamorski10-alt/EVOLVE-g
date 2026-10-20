"""enforce one result row per session exercise set

Revision ID: evolve13setunique
Revises: evolve12active
"""

from alembic import op

revision = "evolve13setunique"
down_revision = "evolve12active"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE UNIQUE INDEX uq_training_set_session_exercise_number "
        "ON training_set_results(session_id, exercise_key, set_number)"
    )


def downgrade():
    op.execute("DROP INDEX uq_training_set_session_exercise_number")
