"""Fix created_at and updated_at defaults

Revision ID: 005_fix_created_at_defaults
Revises: 004_add_time_saved_minutes_to_workflows
Create Date: 2025-08-27 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_fix_created_at_defaults'
down_revision: Union[str, None] = '004_add_time_saved_minutes_to_workflows'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add server defaults for created_at and updated_at columns in metrics_aggregations
    op.alter_column('metrics_aggregations', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    op.alter_column('metrics_aggregations', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    # Add server defaults for created_at and updated_at columns in workflow_trend_metrics
    op.alter_column('workflow_trend_metrics', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    op.alter_column('workflow_trend_metrics', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    # Also fix workflows and workflow_executions if they don't have defaults
    op.alter_column('workflows', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    op.alter_column('workflows', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    op.alter_column('workflow_executions', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)
    
    op.alter_column('workflow_executions', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    existing_nullable=False)


def downgrade() -> None:
    # Remove server defaults
    op.alter_column('workflow_executions', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('workflow_executions', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('workflows', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('workflows', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('workflow_trend_metrics', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('workflow_trend_metrics', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('metrics_aggregations', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)
    
    op.alter_column('metrics_aggregations', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=False)