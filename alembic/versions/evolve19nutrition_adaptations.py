"""Add nutrition adaptation audit trail.

Revision ID: evolve19nutrition_adaptations
Revises: evolve18nutrition
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve19nutrition_adaptations"
down_revision = "evolve18nutrition"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "nutrition_adaptations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("evidence_days", sa.Integer(), nullable=False),
        sa.Column("training_sessions", sa.Integer(), nullable=False),
        sa.Column("base_calories_kcal", sa.Integer(), nullable=False),
        sa.Column("proposed_calories_kcal", sa.Integer(), nullable=False),
        sa.Column("base_protein_g", sa.Integer(), nullable=False),
        sa.Column("proposed_protein_g", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nutrition_adaptations_user_id", "nutrition_adaptations", ["user_id"], unique=False)
    op.create_index("ix_nutrition_adaptations_created_at", "nutrition_adaptations", ["created_at"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_nutrition_adaptations_created_at", table_name="nutrition_adaptations")
    op.drop_index("ix_nutrition_adaptations_user_id", table_name="nutrition_adaptations")
    op.drop_table("nutrition_adaptations")
