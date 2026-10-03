"""Add provenance and uniqueness for session-derived exercise results.

Revision ID: evolve14resultsource
Revises: evolve13setunique
"""

from alembic import op
import sqlalchemy as sa


revision = "evolve14resultsource"
down_revision = "evolve13setunique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercise_results",
        sa.Column("source_session_id", sa.String(), nullable=True),
    )
    op.add_column(
        "exercise_results",
        sa.Column("source_exercise_key", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_exercise_results_source_session_id",
        "exercise_results",
        ["source_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_exercise_results_source_exercise_key",
        "exercise_results",
        ["source_exercise_key"],
        unique=False,
    )
    op.create_index(
        "uq_exercise_result_session_exercise",
        "exercise_results",
        ["source_session_id", "source_exercise_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_exercise_result_session_exercise", table_name="exercise_results")
    op.drop_index("ix_exercise_results_source_exercise_key", table_name="exercise_results")
    op.drop_index("ix_exercise_results_source_session_id", table_name="exercise_results")
    op.drop_column("exercise_results", "source_exercise_key")
    op.drop_column("exercise_results", "source_session_id")
