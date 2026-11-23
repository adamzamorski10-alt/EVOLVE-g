"""add strength experience and dumbbell capability fields to users

Revision ID: evolve33userexperience
Revises: 38d81e29e253
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "evolve33userexperience"
down_revision: Union[str, Sequence[str], None] = "38d81e29e253"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {col["name"] for col in sa.inspect(bind).get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "strength_training_experience" not in existing_columns:
            batch_op.add_column(
                sa.Column("strength_training_experience", sa.String(), nullable=True)
            )
        if "dumbbell_type" not in existing_columns:
            batch_op.add_column(sa.Column("dumbbell_type", sa.String(), nullable=True))
        if "dumbbell_max_kg_per_dumbbell" not in existing_columns:
            batch_op.add_column(
                sa.Column("dumbbell_max_kg_per_dumbbell", sa.Float(), nullable=True)
            )
        if "dumbbell_increment_kg" not in existing_columns:
            batch_op.add_column(
                sa.Column("dumbbell_increment_kg", sa.Float(), nullable=True)
            )


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = {col["name"] for col in sa.inspect(bind).get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "dumbbell_increment_kg" in existing_columns:
            batch_op.drop_column("dumbbell_increment_kg")
        if "dumbbell_max_kg_per_dumbbell" in existing_columns:
            batch_op.drop_column("dumbbell_max_kg_per_dumbbell")
        if "dumbbell_type" in existing_columns:
            batch_op.drop_column("dumbbell_type")
        if "strength_training_experience" in existing_columns:
            batch_op.drop_column("strength_training_experience")
