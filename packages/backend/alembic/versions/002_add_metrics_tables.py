"""Add persistent metrics tables

Revision ID: 002_add_metrics_tables
Revises: 001_initial_migration
Create Date: 2025-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_metrics_tables'
down_revision: Union[str, None] = '001_initial_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('n8n_workflow_id', sa.String(length=255), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('nodes', sa.Integer(), nullable=True),
        sa.Column('connections', sa.Integer(), nullable=True),
        sa.Column('n8n_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('n8n_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflows_id', 'workflows', ['id'])
    op.create_index('ix_workflows_n8n_workflow_id', 'workflows', ['n8n_workflow_id'])
    op.create_index('ix_workflows_client_id', 'workflows', ['client_id'])

    # Create workflow_executions table
    op.create_table('workflow_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('n8n_execution_id', sa.String(length=255), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('SUCCESS', 'ERROR', 'WAITING', 'RUNNING', 'CANCELED', 'CRASHED', 'NEW', name='executionstatus'), nullable=False),
        sa.Column('mode', sa.Enum('MANUAL', 'TRIGGER', 'RETRY', 'WEBHOOK', 'ERROR_TRIGGER', name='executionmode'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('is_production', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('data_size_bytes', sa.Integer(), nullable=True),
        sa.Column('node_count', sa.Integer(), nullable=True),
        sa.Column('retry_of', sa.String(length=255), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('n8n_execution_id')
    )
    op.create_index('ix_workflow_executions_id', 'workflow_executions', ['id'])
    op.create_index('ix_workflow_executions_n8n_execution_id', 'workflow_executions', ['n8n_execution_id'])
    op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('ix_workflow_executions_client_id', 'workflow_executions', ['client_id'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('ix_workflow_executions_started_at', 'workflow_executions', ['started_at'])
    op.create_index('ix_workflow_executions_is_production', 'workflow_executions', ['is_production'])

    # Create metrics_aggregations table
    op.create_table('metrics_aggregations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.Column('period_type', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', name='aggregationperiod'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('total_executions', sa.Integer(), nullable=False),
        sa.Column('successful_executions', sa.Integer(), nullable=False),
        sa.Column('failed_executions', sa.Integer(), nullable=False),
        sa.Column('canceled_executions', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('avg_execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('min_execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('max_execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('total_data_size_bytes', sa.Integer(), nullable=True),
        sa.Column('avg_data_size_bytes', sa.Float(), nullable=True),
        sa.Column('total_workflows', sa.Integer(), nullable=True),
        sa.Column('active_workflows', sa.Integer(), nullable=True),
        sa.Column('most_common_error', sa.String(length=500), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('time_saved_hours', sa.Float(), nullable=True),
        sa.Column('productivity_score', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metrics_aggregations_id', 'metrics_aggregations', ['id'])
    op.create_index('ix_metrics_aggregations_client_id', 'metrics_aggregations', ['client_id'])
    op.create_index('ix_metrics_aggregations_workflow_id', 'metrics_aggregations', ['workflow_id'])
    op.create_index('ix_metrics_aggregations_period_type', 'metrics_aggregations', ['period_type'])
    op.create_index('ix_metrics_aggregations_period_start', 'metrics_aggregations', ['period_start'])

    # Create workflow_trend_metrics table
    op.create_table('workflow_trend_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('executions_count', sa.Integer(), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('avg_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_duration_seconds', sa.Float(), nullable=True),
        sa.Column('success_rate_trend', sa.Float(), nullable=True),
        sa.Column('performance_trend', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_trend_metrics_id', 'workflow_trend_metrics', ['id'])
    op.create_index('ix_workflow_trend_metrics_workflow_id', 'workflow_trend_metrics', ['workflow_id'])
    op.create_index('ix_workflow_trend_metrics_client_id', 'workflow_trend_metrics', ['client_id'])
    op.create_index('ix_workflow_trend_metrics_date', 'workflow_trend_metrics', ['date'])

    # Create composite indexes for better query performance
    op.create_index('ix_workflow_executions_client_date', 'workflow_executions', ['client_id', 'started_at'])
    op.create_index('ix_workflow_executions_workflow_date', 'workflow_executions', ['workflow_id', 'started_at'])
    op.create_index('ix_workflow_executions_production_status', 'workflow_executions', ['is_production', 'status'])
    op.create_index('ix_metrics_aggregations_client_period', 'metrics_aggregations', ['client_id', 'period_type', 'period_start'])
    op.create_index('ix_workflow_trend_metrics_workflow_date', 'workflow_trend_metrics', ['workflow_id', 'date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_workflow_trend_metrics_workflow_date', table_name='workflow_trend_metrics')
    op.drop_index('ix_metrics_aggregations_client_period', table_name='metrics_aggregations')
    op.drop_index('ix_workflow_executions_production_status', table_name='workflow_executions')
    op.drop_index('ix_workflow_executions_workflow_date', table_name='workflow_executions')
    op.drop_index('ix_workflow_executions_client_date', table_name='workflow_executions')

    # Drop tables
    op.drop_table('workflow_trend_metrics')
    op.drop_table('metrics_aggregations')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')

    # Drop enums (PostgreSQL specific)
    # Note: SQLite doesn't support enums, so this will be handled gracefully
    try:
        op.execute('DROP TYPE IF EXISTS executionstatus')
        op.execute('DROP TYPE IF EXISTS executionmode')
        op.execute('DROP TYPE IF EXISTS aggregationperiod')
    except Exception:
        # Ignore errors for SQLite or other databases
        pass