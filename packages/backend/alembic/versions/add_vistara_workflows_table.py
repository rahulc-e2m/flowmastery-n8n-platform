"""add_vistara_workflows_table

Revision ID: add_vistara_workflows_table
Revises: 9087571cea63
Create Date: 2025-09-08 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_vistara_workflows_table'
down_revision = '53f4cebff7c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vistara_categories table first
    op.create_table('vistara_categories',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'name', name='uq_vistara_categories_client_name')
    )
    
    # Create indexes for vistara_categories
    op.create_index(op.f('ix_vistara_categories_id'), 'vistara_categories', ['id'], unique=False)
    op.create_index(op.f('ix_vistara_categories_client_id'), 'vistara_categories', ['client_id'], unique=False)
    op.create_index(op.f('ix_vistara_categories_name'), 'vistara_categories', ['name'], unique=False)
    
    # Create vistara_workflows table
    op.create_table('vistara_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('original_workflow_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('workflow_name', sa.String(length=255), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('documentation_link', sa.String(length=500), nullable=True),
        sa.Column('total_executions', sa.Integer(), nullable=False),
        sa.Column('successful_executions', sa.Integer(), nullable=False),
        sa.Column('failed_executions', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('avg_execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('manual_time_minutes', sa.Integer(), nullable=False),
        sa.Column('time_saved_per_execution_minutes', sa.Integer(), nullable=False),
        sa.Column('total_time_saved_hours', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_execution', sa.DateTime(timezone=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['original_workflow_id'], ['workflows.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['vistara_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_vistara_workflows_id'), 'vistara_workflows', ['id'], unique=False)
    op.create_index(op.f('ix_vistara_workflows_original_workflow_id'), 'vistara_workflows', ['original_workflow_id'], unique=False)
    op.create_index(op.f('ix_vistara_workflows_client_id'), 'vistara_workflows', ['client_id'], unique=False)
    op.create_index(op.f('ix_vistara_workflows_category_id'), 'vistara_workflows', ['category_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_vistara_workflows_category_id'), table_name='vistara_workflows')
    op.drop_index(op.f('ix_vistara_workflows_client_id'), table_name='vistara_workflows')
    op.drop_index(op.f('ix_vistara_workflows_original_workflow_id'), table_name='vistara_workflows')
    op.drop_index(op.f('ix_vistara_workflows_id'), table_name='vistara_workflows')
    
    # Drop table
    op.drop_table('vistara_workflows')
    
    # Drop vistara_categories indexes
    op.drop_index(op.f('ix_vistara_categories_name'), table_name='vistara_categories')
    op.drop_index(op.f('ix_vistara_categories_client_id'), table_name='vistara_categories')
    op.drop_index(op.f('ix_vistara_categories_id'), table_name='vistara_categories')
    
    # Drop vistara_categories table
    op.drop_table('vistara_categories')
