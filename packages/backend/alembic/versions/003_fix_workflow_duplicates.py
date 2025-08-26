"""Fix workflow duplicates by adding unique constraint

Revision ID: 003_fix_workflow_duplicates
Revises: 002_add_metrics_tables
Create Date: 2025-01-26 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_fix_workflow_duplicates'
down_revision: Union[str, None] = '002_add_metrics_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, remove any existing duplicates
    op.execute("""
        DELETE FROM workflows 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM workflows 
            GROUP BY client_id, n8n_workflow_id
        )
    """)
    
    # Add unique constraint to prevent future duplicates
    op.create_unique_constraint(
        'uq_workflows_client_n8n_id',
        'workflows',
        ['client_id', 'n8n_workflow_id']
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint('uq_workflows_client_n8n_id', 'workflows', type_='unique')