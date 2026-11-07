"""add client_id to training_set_results for offline idempotency

Revision ID: evolve32trainingsetclientid
Revises: evolve31authhardening
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "evolve32trainingsetclientid"
down_revision: Union[str, Sequence[str], None] = "evolve31authhardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    existing_cols = {col["name"] for col in insp.get_columns("training_set_results")}
    with op.batch_alter_table("training_set_results") as batch_op:
        if "client_id" not in existing_cols:
            batch_op.add_column(
                sa.Column("client_id", sa.String(length=200), nullable=True)
            )

    existing_indexes = {ix["name"] for ix in insp.get_indexes("training_set_results")}
    if "ix_training_set_results_client_id" not in existing_indexes:
        op.create_index(
            "ix_training_set_results_client_id",
            "training_set_results",
            ["client_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    existing_indexes = {ix["name"] for ix in insp.get_indexes("training_set_results")}
    if "ix_training_set_results_client_id" in existing_indexes:
        op.drop_index("ix_training_set_results_client_id", table_name="training_set_results")

    existing_cols = {col["name"] for col in insp.get_columns("training_set_results")}
    with op.batch_alter_table("training_set_results") as batch_op:
        if "client_id" in existing_cols:
            batch_op.drop_column("client_id")

