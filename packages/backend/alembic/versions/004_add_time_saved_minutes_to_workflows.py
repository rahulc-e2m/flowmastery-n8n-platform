"""Add time_saved_per_execution_minutes to workflows

Revision ID: 004_add_time_saved_minutes_to_workflows
Revises: 003_fix_workflow_duplicates
Create Date: 2025-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_time_saved_minutes_to_workflows'
down_revision: Union[str, None] = '003_fix_workflow_duplicates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'workflows',
        sa.Column('time_saved_per_execution_minutes', sa.Integer(), nullable=False, server_default='30')
    )
    # Remove server_default after setting existing rows
    op.alter_column('workflows', 'time_saved_per_execution_minutes', server_default=None)


def downgrade() -> None:
    op.drop_column('workflows', 'time_saved_per_execution_minutes')


