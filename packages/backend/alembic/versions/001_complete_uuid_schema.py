"""Complete database schema with UUID primary keys

Revision ID: 001_complete_uuid_schema
Revises: 
Create Date: 2025-01-25 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001_complete_uuid_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create complete database schema with UUID primary keys"""
    
    # Enable uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('client_id', UUID(as_uuid=False), nullable=True),
        sa.Column('created_by_admin_id', UUID(as_uuid=False), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Clients table
    op.create_table(
        'clients',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('n8n_api_key_encrypted', sa.Text, nullable=True),
        sa.Column('n8n_api_url', sa.String(500), nullable=True),
        sa.Column('created_by_admin_id', UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Invitations table
    op.create_table(
        'invitations',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('invited_by_admin_id', UUID(as_uuid=False), nullable=False),
        sa.Column('client_id', UUID(as_uuid=False), nullable=True),
        sa.Column('accepted_user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Workflows table
    op.create_table(
        'workflows',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('n8n_workflow_id', sa.String(255), nullable=False, index=True),
        sa.Column('client_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('active', sa.Boolean, default=True, nullable=False),
        sa.Column('tags', sa.Text, nullable=True),
        sa.Column('nodes', sa.Integer, nullable=True),
        sa.Column('connections', sa.Integer, nullable=True),
        sa.Column('n8n_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('n8n_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settings', sa.Text, nullable=True),
        sa.Column('time_saved_per_execution_minutes', sa.Integer, nullable=False, default=30),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('client_id', 'n8n_workflow_id', name='uq_workflows_client_n8n_id')
    )
    
    # Workflow executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('n8n_execution_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('workflow_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('client_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True),
        sa.Column('mode', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
        sa.Column('is_production', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('data_size_bytes', sa.Integer, nullable=True),
        sa.Column('node_count', sa.Integer, nullable=True),
        sa.Column('retry_of', sa.String(255), nullable=True),
        sa.Column('retry_count', sa.Integer, default=0, nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Sync states table
    op.create_table(
        'sync_states',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('client_id', UUID(as_uuid=False), nullable=False, unique=True, index=True),
        sa.Column('last_workflow_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_id', sa.String(255), nullable=True),
        sa.Column('oldest_execution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('newest_execution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_cursor', sa.Text, nullable=True),
        sa.Column('last_daily_aggregation', sa.Date, nullable=True),
        sa.Column('last_weekly_aggregation', sa.Date, nullable=True),
        sa.Column('last_monthly_aggregation', sa.Date, nullable=True),
        sa.Column('total_workflows_synced', sa.Integer, default=0, nullable=False),
        sa.Column('total_executions_synced', sa.Integer, default=0, nullable=False),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Metrics aggregations table
    op.create_table(
        'metrics_aggregations',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('client_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('workflow_id', UUID(as_uuid=False), nullable=True, index=True),
        sa.Column('period_type', sa.String(50), nullable=False, index=True),
        sa.Column('period_start', sa.Date, nullable=False, index=True),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('total_executions', sa.Integer, default=0, nullable=False),
        sa.Column('successful_executions', sa.Integer, default=0, nullable=False),
        sa.Column('failed_executions', sa.Integer, default=0, nullable=False),
        sa.Column('canceled_executions', sa.Integer, default=0, nullable=False),
        sa.Column('success_rate', sa.Float, default=0.0, nullable=False),
        sa.Column('avg_execution_time_seconds', sa.Float, nullable=True),
        sa.Column('min_execution_time_seconds', sa.Float, nullable=True),
        sa.Column('max_execution_time_seconds', sa.Float, nullable=True),
        sa.Column('total_data_size_bytes', sa.Integer, nullable=True),
        sa.Column('avg_data_size_bytes', sa.Float, nullable=True),
        sa.Column('total_workflows', sa.Integer, nullable=True),
        sa.Column('active_workflows', sa.Integer, nullable=True),
        sa.Column('most_common_error', sa.String(500), nullable=True),
        sa.Column('error_count', sa.Integer, default=0, nullable=False),
        sa.Column('time_saved_hours', sa.Float, nullable=True),
        sa.Column('productivity_score', sa.Float, nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Workflow trend metrics table
    op.create_table(
        'workflow_trend_metrics',
        sa.Column('id', UUID(as_uuid=False), primary_key=True, default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('workflow_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('client_id', UUID(as_uuid=False), nullable=False, index=True),
        sa.Column('date', sa.Date, nullable=False, index=True),
        sa.Column('executions_count', sa.Integer, default=0, nullable=False),
        sa.Column('success_count', sa.Integer, default=0, nullable=False),
        sa.Column('error_count', sa.Integer, default=0, nullable=False),
        sa.Column('avg_duration_seconds', sa.Float, nullable=True),
        sa.Column('total_duration_seconds', sa.Float, nullable=True),
        sa.Column('success_rate_trend', sa.Float, nullable=True),
        sa.Column('performance_trend', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    # Create foreign key constraints
    op.create_foreign_key('fk_users_client_id', 'users', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_users_created_by_admin_id', 'users', 'users', ['created_by_admin_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_clients_created_by_admin_id', 'clients', 'users', ['created_by_admin_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_invitations_invited_by_admin_id', 'invitations', 'users', ['invited_by_admin_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_invitations_client_id', 'invitations', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_invitations_accepted_user_id', 'invitations', 'users', ['accepted_user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workflows_client_id', 'workflows', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workflow_executions_workflow_id', 'workflow_executions', 'workflows', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workflow_executions_client_id', 'workflow_executions', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_sync_states_client_id', 'sync_states', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_metrics_aggregations_client_id', 'metrics_aggregations', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_metrics_aggregations_workflow_id', 'metrics_aggregations', 'workflows', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workflow_trend_metrics_workflow_id', 'workflow_trend_metrics', 'workflows', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workflow_trend_metrics_client_id', 'workflow_trend_metrics', 'clients', ['client_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('workflow_trend_metrics')
    op.drop_table('metrics_aggregations')
    op.drop_table('sync_states')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
    op.drop_table('invitations')
    op.drop_table('clients')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')