"""Merge the EVOLVE migration branches during the pre-Stage-6 audit.

Revision ID: evolve20migration_merge
Revises: evolve19nutrition_adaptations, 72efb594294f
"""

revision = "evolve20migration_merge"
down_revision = ("evolve19nutrition_adaptations", "72efb594294f")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
