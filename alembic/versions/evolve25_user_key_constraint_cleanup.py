"""Align PostgreSQL users.user_key constraint with SQLModel metadata.

Revision ID: evolve25userkey
Revises: evolve21active_session_unique
"""
from alembic import op
import sqlalchemy as sa

revision = "evolve25userkey"
down_revision = "evolve21active_session_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Older PostgreSQL schemas retained an implicit UNIQUE constraint from the
    # initial table while current SQLModel metadata represents user_key
    # uniqueness with the named unique index ix_users_user_key. Keeping both
    # causes Alembic check to report a perpetual schema drift.
    if op.get_bind().dialect.name != "postgresql":
        return

    inspector = sa.inspect(op.get_bind())
    constraints = {
        item.get("name")
        for item in inspector.get_unique_constraints("users")
    }
    if "users_user_key_key" in constraints:
        op.drop_constraint("users_user_key_key", "users", type_="unique")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    inspector = sa.inspect(op.get_bind())
    constraints = {
        item.get("name")
        for item in inspector.get_unique_constraints("users")
    }
    if "users_user_key_key" not in constraints:
        op.create_unique_constraint(
            "users_user_key_key",
            "users",
            ["user_key"],
        )
