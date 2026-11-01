"""add per-user training locations

Revision ID: evolve27traininglocations
Revises: evolve26sportprofile
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "evolve27traininglocations"
down_revision: Union[str, Sequence[str], None] = "evolve26sportprofile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "training_locations_json" not in existing:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("training_locations_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "training_locations_json" in existing:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("training_locations_json")
