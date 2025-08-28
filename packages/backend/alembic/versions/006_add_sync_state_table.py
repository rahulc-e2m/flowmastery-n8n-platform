"""Add sync_state table

Revision ID: 006_add_sync_state
Revises: 005_fix_created_at_defaults
Create Date: 2024-12-28 05:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_sync_state'
down_revision = '005_fix_created_at_defaults'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sync_states table
    op.create_table('sync_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('last_workflow_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_id', sa.String(length=255), nullable=True),
        sa.Column('oldest_execution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('newest_execution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_cursor', sa.Text(), nullable=True),
        sa.Column('last_daily_aggregation', sa.Date(), nullable=True),
        sa.Column('last_weekly_aggregation', sa.Date(), nullable=True),
        sa.Column('last_monthly_aggregation', sa.Date(), nullable=True),
        sa.Column('total_workflows_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_executions_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_sync_states_client_id', 'sync_states', ['client_id'], unique=True)
    
    # Create updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_sync_states_updated_at BEFORE UPDATE
        ON sync_states FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_sync_states_updated_at ON sync_states;")
    
    # Drop table
    op.drop_table('sync_states')
