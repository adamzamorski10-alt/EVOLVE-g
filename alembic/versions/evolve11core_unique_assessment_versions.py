"""enforce unique assessment versions per user

Revision ID: evolve11core
Revises: evolve10assessment
"""

from alembic import op

revision = "evolve11core"
down_revision = "evolve10assessment"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assessments") as batch:
        batch.create_unique_constraint(
            "uq_assessments_user_version",
            ["user_id", "assessment_version"],
        )


def downgrade():
    with op.batch_alter_table("assessments") as batch:
        batch.drop_constraint(
            "uq_assessments_user_version",
            type_="unique",
        )
