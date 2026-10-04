"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-04 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. parents
    op.create_table(
        'parents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parents_email'), 'parents', ['email'], unique=True)

    # 2. push_tokens
    op.create_table(
        'push_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_push_tokens_parent_id'), 'push_tokens', ['parent_id'], unique=False)

    # 3. children
    op.create_table(
        'children',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('grade', sa.String(length=100), nullable=False),
        sa.Column('curriculum', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False, server_default='English'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_children_parent_id'), 'children', ['parent_id'], unique=False)

    # 4. consents
    op.create_table(
        'consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=100), nullable=False),
        sa.Column('consented_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('voice', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expression', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('store_reasoning', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('model_improvement', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_child_id'), 'consents', ['child_id'], unique=False)
    op.create_index(op.f('ix_consents_parent_id'), 'consents', ['parent_id'], unique=False)

    # 5. devices
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('pairing_token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='offline'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_child_id'), 'devices', ['child_id'], unique=False)
    op.create_index(op.f('ix_devices_pairing_token'), 'devices', ['pairing_token'], unique=True)

    # 6. controls
    op.create_table(
        'controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('daily_limit_minutes', sa.Integer(), nullable=False, server_default='45'),
        sa.Column('schedule', sa.JSON(), nullable=True),
        sa.Column('paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('subjects_allowed', sa.JSON(), nullable=True),
        sa.Column('content_level', sa.String(length=100), nullable=True),
        sa.Column('tries_before_reveal', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('probe_mode', sa.String(length=50), nullable=False, server_default='both'),
        sa.Column('frustration_guard', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('tries_before_reveal >= 1 AND tries_before_reveal <= 3', name='check_tries_before_reveal_range'),
        sa.CheckConstraint("probe_mode IN ('voice', 'tap', 'both')", name='check_probe_mode_values'),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_controls_child_id'), 'controls', ['child_id'], unique=True)

    # 7. control_acks
    op.create_table(
        'control_acks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('control_version', sa.Integer(), nullable=False),
        sa.Column('acked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_control_acks_device_id'), 'control_acks', ['device_id'], unique=False)

    # 8. sessions
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_mix', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_child_id'), 'sessions', ['child_id'], unique=False)

    # 9. question_attempts
    op.create_table(
        'question_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_picked', sa.String(length=255), nullable=False),
        sa.Column('correct', sa.Boolean(), nullable=False),
        sa.Column('tries_to_correct', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('self_corrected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_attempts_session_id'), 'question_attempts', ['session_id'], unique=False)

    # 10. probe_responses
    op.create_table(
        'probe_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason_text', sa.Text(), nullable=False),
        sa.Column('input_mode', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['question_attempts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_probe_responses_attempt_id'), 'probe_responses', ['attempt_id'], unique=False)

    # 11. mastery
    op.create_table(
        'mastery',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('score >= 0.0 AND score <= 1.0', name='check_mastery_score_range'),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mastery_child_id'), 'mastery', ['child_id'], unique=False)

    # 12. misconceptions
    op.create_table(
        'misconceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('concept', sa.String(length=255), nullable=False),
        sa.Column('child_reason', sa.Text(), nullable=False),
        sa.Column('parent_tip', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_misconceptions_child_id'), 'misconceptions', ['child_id'], unique=False)

    # 13. alerts
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_child_id'), 'alerts', ['child_id'], unique=False)


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('misconceptions')
    op.drop_table('mastery')
    op.drop_table('probe_responses')
    op.drop_table('question_attempts')
    op.drop_table('sessions')
    op.drop_table('control_acks')
    op.drop_table('controls')
    op.drop_table('devices')
    op.drop_table('consents')
    op.drop_table('children')
    op.drop_table('push_tokens')
    op.drop_table('parents')
