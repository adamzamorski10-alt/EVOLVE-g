"""add adaptive plan revision audit

Revision ID: evolve9adapt
Revises: 9d8e7f6a5b43
"""

from alembic import op
import sqlalchemy as sa

revision = "evolve9adapt"
down_revision = "9d8e7f6a5b43"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "adaptive_plan_revisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("source_session_ids_json", sa.Text(), nullable=False),
        sa.Column("previous_plan_json", sa.Text(), nullable=False),
        sa.Column("applied_plan_json", sa.Text(), nullable=False),
        sa.Column("decision_summary_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adaptive_plan_revisions_user_id", "adaptive_plan_revisions", ["user_id"])
    op.create_index("ix_adaptive_plan_revisions_version", "adaptive_plan_revisions", ["version"])
    op.create_index("ix_adaptive_plan_revisions_created_at", "adaptive_plan_revisions", ["created_at"])


def downgrade():
    op.drop_index("ix_adaptive_plan_revisions_created_at", table_name="adaptive_plan_revisions")
    op.drop_index("ix_adaptive_plan_revisions_version", table_name="adaptive_plan_revisions")
    op.drop_index("ix_adaptive_plan_revisions_user_id", table_name="adaptive_plan_revisions")
    op.drop_table("adaptive_plan_revisions")
