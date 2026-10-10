"""Restore the active-session uniqueness invariant after schema sync.

Revision ID: evolve21active_session_unique
Revises: 0d74b80a4276
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve21active_session_unique"
down_revision = "0d74b80a4276"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite and PostgreSQL both support partial unique indexes. Fail closed on
    # other dialects rather than silently shipping without the concurrency guard.
    dialect = op.get_bind().dialect.name
    if dialect not in {"sqlite", "postgresql"}:
        raise RuntimeError(
            "EVOLVE requires SQLite or PostgreSQL partial unique-index support "
            "for uq_training_active_user_day; configure a supported backend "
            "before upgrading."
        )

    op.create_index(
        "uq_training_active_user_day",
        "training_sessions",
        ["user_id", "session_date"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_training_active_user_day", table_name="training_sessions")
