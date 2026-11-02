"""persist basketball athlete profile and assessment

Revision ID: evolve28basketballprofile
Revises: evolve27traininglocations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "evolve28basketballprofile"
down_revision: Union[str, Sequence[str], None] = "evolve27traininglocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "basketball_profile_json" not in existing:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("basketball_profile_json", sa.Text(), nullable=False, server_default="{}"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "basketball_profile_json" in existing:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("basketball_profile_json")
