from alembic import op
import sqlalchemy as sa

revision = "evolve17goalmetrics"
down_revision = "evolve16goals"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("goals", sa.Column("metric_key", sa.String(), nullable=True))
    op.add_column("goals", sa.Column("baseline_value", sa.Float(), nullable=True))
    op.add_column("goals", sa.Column("target_value", sa.Float(), nullable=True))
    op.create_index("ix_goals_metric_key", "goals", ["metric_key"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_goals_metric_key", table_name="goals")
    op.drop_column("goals", "target_value")
    op.drop_column("goals", "baseline_value")
    op.drop_column("goals", "metric_key")
