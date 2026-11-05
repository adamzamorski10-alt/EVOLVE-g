"""auth hardening: token_version, refresh_tokens, password reset, email unique

Revision ID: evolve31authhardening
Revises: evolve30restorelegacyfields
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "evolve31authhardening"
down_revision: Union[str, Sequence[str], None] = "evolve30restorelegacyfields"
branch_labels = None
depends_on = None

_SPORT_INDEXES = (
    "category",
    "client_id",
    "created_at",
    "source",
    "test_run_id",
    "zone",
)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. users columns
    existing_user_cols = {col["name"] for col in insp.get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "token_version" not in existing_user_cols:
            batch_op.add_column(
                sa.Column("token_version", sa.Integer(), nullable=False, server_default="1")
            )
        if "password_reset_token_hash" not in existing_user_cols:
            batch_op.add_column(
                sa.Column("password_reset_token_hash", sa.String(), nullable=True)
            )
        if "password_reset_expires_at" not in existing_user_cols:
            batch_op.add_column(
                sa.Column("password_reset_expires_at", sa.DateTime(), nullable=True)
            )

    # 2. refresh_tokens table
    tables = insp.get_table_names()
    if "refresh_tokens" not in tables:
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("jti", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
        op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
        op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])

    # 3. sport_attempts sync indexes if missing
    if "sport_attempts" in tables:
        existing_indexes = {idx["name"] for idx in insp.get_indexes("sport_attempts")}
        for col_name in _SPORT_INDEXES:
            idx_name = f"ix_sport_attempts_{col_name}"
            if idx_name not in existing_indexes:
                op.create_index(idx_name, "sport_attempts", [col_name])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. drop sport_attempts extra indexes
    if "sport_attempts" in tables:
        existing_indexes = {idx["name"] for idx in insp.get_indexes("sport_attempts")}
        for col_name in reversed(_SPORT_INDEXES):
            idx_name = f"ix_sport_attempts_{col_name}"
            if idx_name in existing_indexes:
                op.drop_index(idx_name, table_name="sport_attempts")

    # 2. drop refresh_tokens
    if "refresh_tokens" in tables:
        op.drop_table("refresh_tokens")

    # 3. drop users columns
    existing_user_cols = {col["name"] for col in insp.get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "password_reset_expires_at" in existing_user_cols:
            batch_op.drop_column("password_reset_expires_at")
        if "password_reset_token_hash" in existing_user_cols:
            batch_op.drop_column("password_reset_token_hash")
        if "token_version" in existing_user_cols:
            batch_op.drop_column("token_version")
