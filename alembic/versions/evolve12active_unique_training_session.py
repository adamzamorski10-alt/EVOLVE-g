"""prevent multiple active training sessions for one user/day

Revision ID: evolve12active
Revises: evolve11core
"""

from alembic import op

revision = "evolve12active"
down_revision = "evolve11core"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE UNIQUE INDEX uq_training_active_user_day "
        "ON training_sessions(user_id, session_date) "
        "WHERE status = 'active'"
    )


def downgrade():
    op.execute("DROP INDEX uq_training_active_user_day")
