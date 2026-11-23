"""Initial database schema with constraints and partial unique indexes

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. companies
    op.create_table(
        'companies',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False, server_default='America/Chicago'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. teams
    op.create_table(
        'teams',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'team_member', 'observer')", name='chk_user_role'),
    )

    # 4. team_memberships
    op.create_table(
        'team_memberships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'team_id', name='uq_user_team_membership'),
    )

    # 5. measurables
    op.create_table(
        'measurables',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('goal_type', sa.String(), nullable=False),
        sa.Column('goal_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('goal_min', sa.Numeric(12, 2), nullable=True),
        sa.Column('goal_max', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("goal_type IN ('at_least', 'at_most', 'between', 'exactly')", name='chk_measurable_goal_type'),
        sa.CheckConstraint(
            "(goal_type != 'between' AND goal_value IS NOT NULL) OR (goal_type = 'between' AND goal_min IS NOT NULL AND goal_max IS NOT NULL AND goal_min <= goal_max)",
            name='chk_measurable_goal_definition'
        ),
    )

    # 6. scores
    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('measurable_id', sa.String(), sa.ForeignKey('measurables.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('value', sa.Numeric(12, 2), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('measurable_id', 'week_start', name='uq_measurable_week_score'),
    )

    # 7. rocks
    op.create_table(
        'rocks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('quarter', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('on_track', 'off_track', 'complete')", name='chk_rock_status'),
    )

    # 8. milestones
    op.create_table(
        'milestones',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('rock_id', sa.String(), sa.ForeignKey('rocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('done', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 9. issues
    op.create_table(
        'issues',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('source_measurable_id', sa.String(), sa.ForeignKey('measurables.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_week_start', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('solved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.CheckConstraint("priority IS NULL OR (priority >= 1 AND priority <= 5)", name='chk_issue_priority'),
        sa.CheckConstraint(
            "(source_measurable_id IS NULL AND source_week_start IS NULL) OR (source_measurable_id IS NOT NULL AND source_week_start IS NOT NULL)",
            name='chk_issue_source_integrity'
        ),
        sa.CheckConstraint(
            "solved_at IS NULL OR (solved_at IS NOT NULL AND resolution_note IS NOT NULL)",
            name='chk_issue_solved_note_required'
        ),
    )
    # Partial unique index for duplicate-free unsolved issues
    op.create_index(
        'uq_unsolved_source_issue',
        'issues',
        ['source_measurable_id', 'source_week_start'],
        unique=True,
        postgresql_where=sa.text('solved_at IS NULL AND source_measurable_id IS NOT NULL')
    )

    # 10. todos
    op.create_table(
        'todos',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_issue_id', sa.String(), sa.ForeignKey('issues.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('done_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 11. meetings
    op.create_table(
        'meetings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('facilitator_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_section', sa.String(), server_default='scorecard', nullable=False),
        sa.Column('section_started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("current_section IN ('scorecard', 'ids', 'conclude', 'ended')", name='chk_meeting_current_section'),
    )
    # Partial unique index for single active meeting per team
    op.create_index(
        'uq_active_team_meeting',
        'meetings',
        ['team_id'],
        unique=True,
        postgresql_where=sa.text('ended_at IS NULL')
    )

    # 12. meeting_attendees
    op.create_table(
        'meeting_attendees',
        sa.Column('meeting_id', sa.String(), sa.ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 13. meeting_ratings
    op.create_table(
        'meeting_ratings',
        sa.Column('meeting_id', sa.String(), sa.ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 10', name='chk_meeting_rating_range'),
    )


def downgrade() -> None:
    op.drop_table('meeting_ratings')
    op.drop_table('meeting_attendees')
    op.drop_index('uq_active_team_meeting', table_name='meetings')
    op.drop_table('meetings')
    op.drop_table('todos')
    op.drop_index('uq_unsolved_source_issue', table_name='issues')
    op.drop_table('issues')
    op.drop_table('milestones')
    op.drop_table('rocks')
    op.drop_table('scores')
    op.drop_table('measurables')
    op.drop_table('team_memberships')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('companies')
