from alembic import op
import sqlalchemy as sa

revision = "evolve16goals"
down_revision = "evolve15adaptiveunique"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("goals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("goal_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, cols in (("user_id", ["user_id"]),("goal_type", ["goal_type"]),("status", ["status"]),("start_date", ["start_date"]),("target_date", ["target_date"]),("created_at", ["created_at"]),("updated_at", ["updated_at"])):
        op.create_index(f"ix_goals_{name}", "goals", cols, unique=False)

def downgrade() -> None:
    for name in ("updated_at","created_at","target_date","start_date","status","goal_type","user_id"):
        op.drop_index(f"ix_goals_{name}", table_name="goals")
    op.drop_table("goals")
