"""add exercise_progressions table

Revision ID: 38d81e29e253
Revises: evolve32trainingsetclientid
Create Date: 2026-11-16 19:40:54.268433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38d81e29e253'
down_revision: Union[str, Sequence[str], None] = 'evolve32trainingsetclientid'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table('exercise_progressions'):
        op.create_table(
            'exercise_progressions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('exercise_key', sa.String(length=200), nullable=False),
            sa.Column('exercise_name', sa.String(length=200), nullable=False, server_default=''),
            sa.Column('working_weight_kg', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('current_reps', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reps_at_current_weight', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('sessions_without_progress', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('target_reps_min', sa.Integer(), nullable=False, server_default='8'),
            sa.Column('target_reps_max', sa.Integer(), nullable=False, server_default='12'),
            sa.Column('target_rir', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('calibrated', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('last_session_date', sa.Date(), nullable=True),
            sa.Column('deload_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'exercise_key', name='uq_exercise_progressions_user_key')
        )
        op.create_index('ix_exercise_progressions_exercise_key', 'exercise_progressions', ['exercise_key'], unique=False)
        op.create_index('ix_exercise_progressions_last_session_date', 'exercise_progressions', ['last_session_date'], unique=False)
        op.create_index('ix_exercise_progressions_user_id', 'exercise_progressions', ['user_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table('exercise_progressions'):
        existing_indexes = {ix['name'] for ix in insp.get_indexes('exercise_progressions')}
        for idx in ['ix_exercise_progressions_exercise_key', 'ix_exercise_progressions_last_session_date', 'ix_exercise_progressions_user_id']:
            if idx in existing_indexes:
                op.drop_index(idx, table_name='exercise_progressions')
        op.drop_table('exercise_progressions')
