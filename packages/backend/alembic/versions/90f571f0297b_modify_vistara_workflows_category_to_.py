"""modify_vistara_workflows_category_to_category_id

Revision ID: 90f571f0297b
Revises: add_vistara_workflows_table
Create Date: 2025-09-08 10:50:28.393200

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '90f571f0297b'
down_revision = 'add_vistara_workflows_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category_id column
    op.add_column('vistara_workflows', sa.Column('category_id', postgresql.UUID(as_uuid=False), nullable=True))
    
    # Add foreign key constraint for category_id
    op.create_foreign_key('fk_vistara_workflows_category_id', 'vistara_workflows', 'vistara_categories', ['category_id'], ['id'], ondelete='SET NULL')
    
    # Create index for category_id
    op.create_index(op.f('ix_vistara_workflows_category_id'), 'vistara_workflows', ['category_id'], unique=False)
    
    # Drop the old category column
    op.drop_column('vistara_workflows', 'category')


def downgrade() -> None:
    # Add back category column with enum type
    op.add_column('vistara_workflows', sa.Column('category', sa.Enum('automation', 'integration', 'data_processing', 'reporting', 'communication', 'monitoring', name='workflowcategory'), nullable=False))
    
    # Drop foreign key constraint and index for category_id
    op.drop_index(op.f('ix_vistara_workflows_category_id'), table_name='vistara_workflows')
    op.drop_constraint('fk_vistara_workflows_category_id', 'vistara_workflows', type_='foreignkey')
    
    # Drop category_id column
    op.drop_column('vistara_workflows', 'category_id')
