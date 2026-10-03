"""Restore the missing migration revision referenced by 9d8e7f6a5b43.

This is intentionally a schema no-op. The repository contains the initial
drill_results table in f9fd63cba750 and the subsequent 9d8e7f6a5b43 migration
only adds drill metadata columns. The original 7a6d4c3e9b12 file is absent,
but 9d8e7f6a5b43 still references it, which makes the Alembic graph unloadable.

Keeping the historical revision ID as a no-op preserves the declared parent
relationship without inventing undocumented schema changes.
"""

revision = "7a6d4c3e9b12"
down_revision = "c8b1f3d9a77d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
