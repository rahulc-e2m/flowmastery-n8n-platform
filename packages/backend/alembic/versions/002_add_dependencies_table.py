"""Add dependencies table

Revision ID: 002_add_dependencies_table
Revises: 001_complete_uuid_schema
Create Date: 2024-08-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_dependencies_table'
down_revision = '001_complete_uuid_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dependencies table
    op.create_table('dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform_name', sa.String(length=255), nullable=False),
        sa.Column('where_to_get', sa.Text(), nullable=True, comment='URL where users can get API keys/credentials'),
        sa.Column('guide_link', sa.Text(), nullable=True, comment='Link to step-by-step guide'),
        sa.Column('documentation_link', sa.Text(), nullable=True, comment='Link to official documentation'),
        sa.Column('description', sa.Text(), nullable=True, comment='Brief description of the platform'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique constraint on platform_name
    op.create_unique_constraint('uq_dependencies_platform_name', 'dependencies', ['platform_name'])
    
    # Create index for faster searches
    op.create_index('ix_dependencies_platform_name', 'dependencies', ['platform_name'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_dependencies_platform_name', table_name='dependencies')
    
    # Drop constraints
    op.drop_constraint('uq_dependencies_platform_name', 'dependencies', type_='unique')
    
    # Drop table
    op.drop_table('dependencies')