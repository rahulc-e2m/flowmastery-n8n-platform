"""Add chatbots table

Revision ID: 003_add_chatbots_table
Revises: 002_add_dependencies_table
Create Date: 2024-08-29 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_chatbots_table'
down_revision = '002_add_dependencies_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chatbots table
    op.create_table('chatbots',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('webhook_url', sa.String(length=1000), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_chatbots_id', 'chatbots', ['id'])
    op.create_index('ix_chatbots_name', 'chatbots', ['name'])
    op.create_index('ix_chatbots_client_id', 'chatbots', ['client_id'])
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_chatbots_client_id', 
        'chatbots', 
        'clients', 
        ['client_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_chatbots_created_by_user_id', 
        'chatbots', 
        'users', 
        ['created_by_user_id'], 
        ['id'], 
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_chatbots_created_by_user_id', 'chatbots', type_='foreignkey')
    op.drop_constraint('fk_chatbots_client_id', 'chatbots', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_chatbots_client_id', table_name='chatbots')
    op.drop_index('ix_chatbots_name', table_name='chatbots')
    op.drop_index('ix_chatbots_id', table_name='chatbots')
    
    # Drop table
    op.drop_table('chatbots')