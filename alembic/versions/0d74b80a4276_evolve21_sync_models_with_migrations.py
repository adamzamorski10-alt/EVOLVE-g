"""evolve21_sync_models_with_migrations

Revision ID: 0d74b80a4276
Revises: evolve20migration_merge
Create Date: 2026-10-04 12:56:59.643375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0d74b80a4276'
down_revision: Union[str, Sequence[str], None] = 'evolve20migration_merge'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_number_sequence',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sqlmodel.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )

    with op.batch_alter_table('adaptive_plan_revisions') as batch_op:
        batch_op.alter_column('source_session_ids_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)
        batch_op.alter_column('previous_plan_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)
        batch_op.alter_column('applied_plan_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)
        batch_op.alter_column('decision_summary_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)

    op.drop_index(op.f('uq_adaptive_plan_revision_user_version'), table_name='adaptive_plan_revisions')

    with op.batch_alter_table('assessments') as batch_op:
        batch_op.alter_column('assessment_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)
        batch_op.alter_column('notes',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)

    with op.batch_alter_table('daily_logs') as batch_op:
        batch_op.alter_column('log_date',
                   existing_type=sa.VARCHAR(),
                   type_=sa.Date(),
                   existing_nullable=False)
        batch_op.alter_column('meals_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('workouts_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('custom_meals_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('logged_at',
                   existing_type=sa.VARCHAR(),
                   type_=sa.DateTime(),
                   existing_nullable=False)
        batch_op.drop_column('waist_cm')
        batch_op.drop_column('eaten_meals_json')
        batch_op.drop_column('photo_path')
        batch_op.drop_column('chest_cm')
        batch_op.drop_column('sleep_duration_minutes')

    op.drop_index(op.f('ix_daily_logs_user_date'), table_name='daily_logs')

    with op.batch_alter_table('drill_results') as batch_op:
        batch_op.alter_column('session_date',
                   existing_type=sa.VARCHAR(),
                   type_=sa.Date(),
                   existing_nullable=False)
        batch_op.alter_column('logged_at',
                   existing_type=sa.VARCHAR(),
                   type_=sa.DateTime(),
                   existing_nullable=False)

    op.drop_index(op.f('ix_drill_results_user_date'), table_name='drill_results')

    with op.batch_alter_table('exercise_results') as batch_op:
        batch_op.alter_column('session_date',
                   existing_type=sa.VARCHAR(),
                   type_=sa.Date(),
                   existing_nullable=False)
        batch_op.alter_column('logged_at',
                   existing_type=sa.VARCHAR(),
                   type_=sa.DateTime(),
                   existing_nullable=False)

    op.drop_index(op.f('ix_exercise_results_user_date'), table_name='exercise_results')
    op.drop_index(op.f('ix_exercise_results_user_name'), table_name='exercise_results')
    op.drop_index(op.f('uq_exercise_result_session_exercise'), table_name='exercise_results')
    with op.batch_alter_table('exercise_results') as batch_op:
        batch_op.create_foreign_key('fk_exercise_results_source_session_id', 'training_sessions', ['source_session_id'], ['id'])

    with op.batch_alter_table('training_sessions') as batch_op:
        batch_op.alter_column('planned_snapshot_json',
                   existing_type=sa.TEXT(),
                   type_=sqlmodel.AutoString(),
                   existing_nullable=False)

    op.drop_index(op.f('uq_training_active_user_day'), table_name='training_sessions', sqlite_where=sa.text("status = 'active'"))
    op.drop_index(op.f('uq_training_set_session_exercise_number'), table_name='training_set_results')

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('nickname', sqlmodel.AutoString(), nullable=True))
        batch_op.alter_column('created_at',
                   existing_type=sa.VARCHAR(),
                   type_=sa.DateTime(),
                   existing_nullable=False)
        batch_op.alter_column('updated_at',
                   existing_type=sa.VARCHAR(),
                   type_=sa.DateTime(),
                   existing_nullable=False)
        batch_op.drop_column('level')
        batch_op.drop_column('xp_total')

    op.drop_index(op.f('ix_users_user_key'), table_name='users')
    op.create_index(op.f('ix_users_user_key'), 'users', ['user_key'], unique=True)
    op.create_index(op.f('ix_users_nickname'), 'users', ['nickname'], unique=True)
    op.create_index(op.f('ix_users_user_number'), 'users', ['user_number'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('xp_total', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('level', sa.INTEGER(), nullable=True))

    op.drop_index(op.f('ix_users_user_number'), table_name='users')
    op.drop_index(op.f('ix_users_nickname'), table_name='users')
    op.drop_index(op.f('ix_users_user_key'), table_name='users')
    op.create_index(op.f('ix_users_user_key'), 'users', ['user_key'], unique=False)

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('updated_at',
                   existing_type=sa.DateTime(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)
        batch_op.alter_column('created_at',
                   existing_type=sa.DateTime(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)
        batch_op.drop_column('nickname')

    op.create_index(op.f('uq_training_set_session_exercise_number'), 'training_set_results', ['session_id', 'exercise_key', 'set_number'], unique=1)
    op.create_index(op.f('uq_training_active_user_day'), 'training_sessions', ['user_id', 'session_date'], unique=1, sqlite_where=sa.text("status = 'active'"))

    with op.batch_alter_table('training_sessions') as batch_op:
        batch_op.alter_column('planned_snapshot_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)

    op.drop_constraint('fk_exercise_results_source_session_id', 'exercise_results', type_='foreignkey')
    op.create_index(op.f('uq_exercise_result_session_exercise'), 'exercise_results', ['source_session_id', 'source_exercise_key'], unique=1)
    op.create_index(op.f('ix_exercise_results_user_name'), 'exercise_results', ['user_id', 'exercise_name'], unique=False)
    op.create_index(op.f('ix_exercise_results_user_date'), 'exercise_results', ['user_id', 'session_date'], unique=False)

    with op.batch_alter_table('exercise_results') as batch_op:
        batch_op.alter_column('logged_at',
                   existing_type=sa.DateTime(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)
        batch_op.alter_column('session_date',
                   existing_type=sa.Date(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)

    op.create_index(op.f('ix_drill_results_user_date'), 'drill_results', ['user_id', 'session_date'], unique=False)

    with op.batch_alter_table('drill_results') as batch_op:
        batch_op.alter_column('logged_at',
                   existing_type=sa.DateTime(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)
        batch_op.alter_column('session_date',
                   existing_type=sa.Date(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)

    op.add_column('daily_logs', sa.Column('sleep_duration_minutes', sa.INTEGER(), nullable=True))
    op.add_column('daily_logs', sa.Column('chest_cm', sa.FLOAT(), nullable=True))
    op.add_column('daily_logs', sa.Column('photo_path', sa.VARCHAR(), nullable=True))
    op.add_column('daily_logs', sa.Column('eaten_meals_json', sa.VARCHAR(), nullable=False))
    op.add_column('daily_logs', sa.Column('waist_cm', sa.FLOAT(), nullable=True))
    op.create_index(op.f('ix_daily_logs_user_date'), 'daily_logs', ['user_id', 'log_date'], unique=False)

    with op.batch_alter_table('daily_logs') as batch_op:
        batch_op.alter_column('logged_at',
                   existing_type=sa.DateTime(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)
        batch_op.alter_column('custom_meals_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('workouts_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('meals_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False,
                   existing_server_default=sa.text("'[]'"))
        batch_op.alter_column('log_date',
                   existing_type=sa.Date(),
                   type_=sa.VARCHAR(),
                   existing_nullable=False)

    with op.batch_alter_table('assessments') as batch_op:
        batch_op.alter_column('notes',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)
        batch_op.alter_column('assessment_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)

    op.create_index(op.f('uq_adaptive_plan_revision_user_version'), 'adaptive_plan_revisions', ['user_id', 'version'], unique=1)

    with op.batch_alter_table('adaptive_plan_revisions') as batch_op:
        batch_op.alter_column('decision_summary_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)
        batch_op.alter_column('applied_plan_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)
        batch_op.alter_column('previous_plan_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)
        batch_op.alter_column('source_session_ids_json',
                   existing_type=sqlmodel.AutoString(),
                   type_=sa.TEXT(),
                   existing_nullable=False)

    op.drop_table('user_number_sequence')
