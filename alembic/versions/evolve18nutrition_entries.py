"""Add structured user-owned nutrition intake entries.

Revision ID: evolve18nutrition
Revises: evolve17goalmetrics
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve18nutrition"
down_revision = "evolve17goalmetrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nutrition_entries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=False),
        sa.Column("meal_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("calories_kcal", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("fiber_g", sa.Float(), nullable=False),
        sa.Column("water_liters", sa.Float(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nutrition_entries_user_id", "nutrition_entries", ["user_id"], unique=False)
    op.create_index("ix_nutrition_entries_consumed_at", "nutrition_entries", ["consumed_at"], unique=False)
    op.create_index("ix_nutrition_entries_meal_type", "nutrition_entries", ["meal_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_nutrition_entries_meal_type", table_name="nutrition_entries")
    op.drop_index("ix_nutrition_entries_consumed_at", table_name="nutrition_entries")
    op.drop_index("ix_nutrition_entries_user_id", table_name="nutrition_entries")
    op.drop_table("nutrition_entries")
