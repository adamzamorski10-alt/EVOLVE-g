"""create training execution tables

Revision ID: evolve11training
Revises: evolve11core
"""

from alembic import op
import sqlalchemy as sa

revision = "evolve11training"
down_revision = "evolve11core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("planned_snapshot_json", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("final_rpe", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_sessions_user_id", "training_sessions", ["user_id"], unique=False)
    op.create_index("ix_training_sessions_session_date", "training_sessions", ["session_date"], unique=False)
    op.create_index("ix_training_sessions_status", "training_sessions", ["status"], unique=False)

    op.create_table(
        "training_set_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("exercise_key", sa.String(), nullable=False),
        sa.Column("exercise_name", sa.String(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("planned_reps", sa.Integer(), nullable=True),
        sa.Column("planned_weight_kg", sa.Float(), nullable=True),
        sa.Column("actual_reps", sa.Integer(), nullable=False),
        sa.Column("actual_weight_kg", sa.Float(), nullable=False),
        sa.Column("actual_rpe", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["training_sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_set_results_session_id", "training_set_results", ["session_id"], unique=False)
    op.create_index("ix_training_set_results_user_id", "training_set_results", ["user_id"], unique=False)
    op.create_index("ix_training_set_results_exercise_key", "training_set_results", ["exercise_key"], unique=False)


def downgrade() -> None:
    op.drop_table("training_set_results")
    op.drop_table("training_sessions")
