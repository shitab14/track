"""Meeting summary snapshot and in-meeting attribution (ADR0010)

Adds:
  - meetings.summary_snapshot  : frozen summary captured at conclusion
  - issues.solved_in_meeting_id: meeting an issue was solved in (if any)
  - todos.created_in_meeting_id: meeting a to-do was created in (if any)

All nullable; seeded rows leave them null and fall back to computed summaries.

Revision ID: 0002_meeting_summary
Revises: 0001_initial_schema
Create Date: 2026-11-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_meeting_summary'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('meetings', sa.Column('summary_snapshot', sa.JSON(), nullable=True))

    op.add_column('issues', sa.Column('solved_in_meeting_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_issues_solved_in_meeting', 'issues', 'meetings',
        ['solved_in_meeting_id'], ['id'], ondelete='SET NULL',
    )

    op.add_column('todos', sa.Column('created_in_meeting_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_todos_created_in_meeting', 'todos', 'meetings',
        ['created_in_meeting_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_todos_created_in_meeting', 'todos', type_='foreignkey')
    op.drop_column('todos', 'created_in_meeting_id')

    op.drop_constraint('fk_issues_solved_in_meeting', 'issues', type_='foreignkey')
    op.drop_column('issues', 'solved_in_meeting_id')

    op.drop_column('meetings', 'summary_snapshot')
