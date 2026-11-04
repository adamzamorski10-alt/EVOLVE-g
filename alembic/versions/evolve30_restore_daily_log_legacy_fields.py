"""restore daily log fields required by the legacy API

Revision ID: evolve30restorelegacyfields
Revises: evolve29sportattempts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "evolve30restorelegacyfields"
down_revision: Union[str, Sequence[str], None] = "evolve29sportattempts"
branch_labels = None
depends_on = None

_COLUMNS = {
    "sleep_duration_minutes": sa.Integer(),
    "training_rpe": sa.Integer(),
    "waist_cm": sa.Float(),
    "chest_cm": sa.Float(),
    "photo_path": sa.String(),
    "eaten_meals_json": sa.String(),
}


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("daily_logs")}
    with op.batch_alter_table("daily_logs") as batch_op:
        for name, column_type in _COLUMNS.items():
            if name not in existing:
                default = "[]" if name == "eaten_meals_json" else None
                batch_op.add_column(
                    sa.Column(
                        name,
                        column_type,
                        nullable=name != "eaten_meals_json",
                        server_default=default,
                    )
                )


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("daily_logs")}
    with op.batch_alter_table("daily_logs") as batch_op:
        for name in reversed(tuple(_COLUMNS)):
            if name in existing:
                batch_op.drop_column(name)
