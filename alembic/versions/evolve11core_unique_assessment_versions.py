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
    op.create_unique_constraint(
        "uq_assessments_user_version",
        "assessments",
        ["user_id", "assessment_version"],
    )


def downgrade():
    op.drop_constraint(
        "uq_assessments_user_version",
        "assessments",
        type_="unique",
    )
