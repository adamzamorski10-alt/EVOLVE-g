"""add sport profile fields to users

Revision ID: evolve26sportprofile
Revises: evolve25userkey
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "evolve26sportprofile"
down_revision: Union[str, Sequence[str], None] = "evolve25userkey"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "basketball_position" not in existing_columns:
            batch_op.add_column(sa.Column("basketball_position", sa.String(), nullable=True))
        if "training_experience" not in existing_columns:
            batch_op.add_column(sa.Column("training_experience", sa.String(), nullable=True))
        if "equipment" not in existing_columns:
            batch_op.add_column(sa.Column("equipment", sa.String(), nullable=True))
        if "health_limitations" not in existing_columns:
            batch_op.add_column(sa.Column("health_limitations", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "health_limitations" in existing_columns:
            batch_op.drop_column("health_limitations")
        if "equipment" in existing_columns:
            batch_op.drop_column("equipment")
        if "training_experience" in existing_columns:
            batch_op.drop_column("training_experience")
        if "basketball_position" in existing_columns:
            batch_op.drop_column("basketball_position")
