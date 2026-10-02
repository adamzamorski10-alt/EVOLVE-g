"""add versioned assessments

Revision ID: evolve10assessment
Revises: evolve9adapt
"""

from alembic import op
import sqlalchemy as sa

revision = "evolve10assessment"
down_revision = "evolve9adapt"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("assessment_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("training_level", sa.String(), nullable=True),
        sa.Column("training_experience_years", sa.Float(), nullable=True),
        sa.Column("sessions_per_week", sa.Integer(), nullable=True),
        sa.Column("availability_hours_per_week", sa.Float(), nullable=True),
        sa.Column("recovery_score", sa.Integer(), nullable=True),
        sa.Column("basketball_level", sa.String(), nullable=True),
        sa.Column("shooting_pct", sa.Float(), nullable=True),
        sa.Column("free_throw_pct", sa.Float(), nullable=True),
        sa.Column("sprint_30m_seconds", sa.Float(), nullable=True),
        sa.Column("vertical_jump_cm", sa.Float(), nullable=True),
        sa.Column("assessment_json", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"])
    op.create_index("ix_assessments_status", "assessments", ["status"])
    op.create_index("ix_assessments_assessment_date", "assessments", ["assessment_date"])
    op.create_index("ix_assessments_created_at", "assessments", ["created_at"])


def downgrade():
    op.drop_index("ix_assessments_created_at", table_name="assessments")
    op.drop_index("ix_assessments_assessment_date", table_name="assessments")
    op.drop_index("ix_assessments_status", table_name="assessments")
    op.drop_index("ix_assessments_user_id", table_name="assessments")
    op.drop_table("assessments")
