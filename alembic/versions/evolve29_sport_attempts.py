"""add canonical sport attempts

Revision ID: evolve29sportattempts
Revises: evolve28basketballprofile
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "evolve29sportattempts"
down_revision: Union[str, Sequence[str], None] = "evolve28basketballprofile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "sport_attempts" not in tables:
        op.create_table(
            "sport_attempts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("attempt_date", sa.Date(), nullable=False),
            sa.Column("source", sa.String(), nullable=False, server_default="manual"),
            sa.Column("test_run_id", sa.String(), nullable=True),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("zone", sa.String(), nullable=True),
            sa.Column("made", sa.Integer(), nullable=True),
            sa.Column("attempts", sa.Integer(), nullable=True),
            sa.Column("errors", sa.Integer(), nullable=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(), nullable=True),
            sa.Column("drill_name", sa.String(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("client_id", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("user_id", "client_id", name="uq_sport_attempts_user_client"),
        )
        op.create_index("ix_sport_attempts_user_id", "sport_attempts", ["user_id"])
        op.create_index("ix_sport_attempts_attempt_date", "sport_attempts", ["attempt_date"])
        op.create_index("ix_sport_attempts_user_date", "sport_attempts", ["user_id", "attempt_date"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "sport_attempts" in tables:
        existing_indexes = {idx["name"] for idx in insp.get_indexes("sport_attempts")}
        if "ix_sport_attempts_user_date" in existing_indexes:
            op.drop_index("ix_sport_attempts_user_date", table_name="sport_attempts")
        if "ix_sport_attempts_attempt_date" in existing_indexes:
            op.drop_index("ix_sport_attempts_attempt_date", table_name="sport_attempts")
        if "ix_sport_attempts_user_id" in existing_indexes:
            op.drop_index("ix_sport_attempts_user_id", table_name="sport_attempts")
        op.drop_table("sport_attempts")
