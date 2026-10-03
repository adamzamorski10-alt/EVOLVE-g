"""Initial schema: users, daily_logs, exercise_results, drill_results.

Revision ID: f9fd63cba750
Revises:
Create Date: 2026-05-13 18:55:19.752581

This revision is the clean-install root of the legacy schema.  The previous
file was an inverted autogenerate diff that assumed the tables already
existed, which made a fresh Alembic database impossible to upgrade.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9fd63cba750"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_key", sa.String(), nullable=False),
        sa.Column("identity_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("start_weight", sa.Float(), nullable=False),
        sa.Column("target_weight", sa.Float(), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("goal", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("diet", sa.String(), nullable=False),
        sa.Column("allergies", sa.String(), nullable=False),
        sa.Column("meals_per_day", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("calories_target", sa.Integer(), nullable=False),
        sa.Column("protein_target", sa.Integer(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False),
        sa.Column("linked_discord_id", sa.String(), nullable=True),
        sa.Column("sports_json", sa.String(), nullable=False),
        sa.Column("training_focus_json", sa.String(), nullable=False),
        sa.Column("improvement_areas_json", sa.String(), nullable=False),
        sa.Column("preferred_foods_json", sa.String(), nullable=False),
        sa.Column("avoid_foods_json", sa.String(), nullable=False),
        sa.Column("available_equipment_json", sa.String(), nullable=False),
        sa.Column("avoid_exercises_json", sa.String(), nullable=False),
        sa.Column("reminders_json", sa.String(), nullable=False),
        sa.Column("weekly_plan_json", sa.String(), nullable=True),
        sa.Column("substitutes_history_json", sa.String(), nullable=False),
        sa.Column("sport_focus", sa.String(), nullable=True),
        sa.Column("sport_specialization", sa.String(), nullable=True),
        sa.Column("sport_training_days_json", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("user_number", sa.Integer(), nullable=True),
        sa.Column("total_xp", sa.Integer(), nullable=False),
        sa.Column("injuries", sa.String(), nullable=False),
        sa.Column("last_weight_change", sa.Float(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.Column("xp_total", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key"),
    )
    op.create_index("ix_users_user_key", "users", ["user_key"], unique=False)
    op.create_index("ix_users_identity_id", "users", ["identity_id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("log_date", sa.String(), nullable=False),
        sa.Column("food", sa.String(), nullable=False),
        sa.Column("workout", sa.String(), nullable=False),
        sa.Column("mood", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("water_liters", sa.Float(), nullable=True),
        sa.Column("sleep_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("waist_cm", sa.Float(), nullable=True),
        sa.Column("chest_cm", sa.Float(), nullable=True),
        sa.Column("photo_path", sa.String(), nullable=True),
        sa.Column("eaten_meals_json", sa.String(), nullable=False),
        sa.Column("logged_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_logs_user_id", "daily_logs", ["user_id"], unique=False)
    op.create_index("ix_daily_logs_log_date", "daily_logs", ["log_date"], unique=False)
    op.create_index("ix_daily_logs_user_date", "daily_logs", ["user_id", "log_date"], unique=False)

    op.create_table(
        "exercise_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("exercise_name", sa.String(), nullable=False),
        sa.Column("session_date", sa.String(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("logged_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exercise_results_user_id", "exercise_results", ["user_id"], unique=False)
    op.create_index("ix_exercise_results_exercise_name", "exercise_results", ["exercise_name"], unique=False)
    op.create_index("ix_exercise_results_session_date", "exercise_results", ["session_date"], unique=False)
    op.create_index("ix_exercise_results_user_date", "exercise_results", ["user_id", "session_date"], unique=False)
    op.create_index("ix_exercise_results_user_name", "exercise_results", ["user_id", "exercise_name"], unique=False)

    op.create_table(
        "drill_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("drill_name", sa.String(), nullable=False),
        sa.Column("session_date", sa.String(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("total_attempts", sa.Integer(), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("time_seconds", sa.Float(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("logged_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drill_results_user_id", "drill_results", ["user_id"], unique=False)
    op.create_index("ix_drill_results_drill_name", "drill_results", ["drill_name"], unique=False)
    op.create_index("ix_drill_results_session_date", "drill_results", ["session_date"], unique=False)
    op.create_index("ix_drill_results_user_date", "drill_results", ["user_id", "session_date"], unique=False)


def downgrade() -> None:
    op.drop_table("drill_results")
    op.drop_table("exercise_results")
    op.drop_table("daily_logs")
    op.drop_table("users")
