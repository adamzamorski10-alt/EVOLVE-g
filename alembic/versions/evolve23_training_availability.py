"""Persist weekly training availability on user profiles.

Revision ID: evolve23_training_availability
Revises: evolve22adaptive_audit
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve23_training_availability"
down_revision = "evolve22adaptive_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("training_availability_json", sa.String(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("users", "training_availability_json")
