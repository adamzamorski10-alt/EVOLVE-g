"""Persist reserved sports-training time windows.

Revision ID: evolve24_sport_training_schedule
Revises: evolve23_training_availability
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve24_sport_training_schedule"
down_revision = "evolve23_training_availability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("sport_training_schedule_json", sa.String(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("users", "sport_training_schedule_json")
