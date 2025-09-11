"""Make Vistara categories global for admin use

Revision ID: 20250908_global_vistara_categories
Revises: [previous_revision_id]
Create Date: 2025-09-08 13:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20250908_global_vistara_categories'
down_revision = None  # Update this to the latest revision ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make client_id nullable and update constraints for global Vistara categories."""
    
    # Drop the existing unique constraint
    op.drop_constraint('uq_vistara_categories_client_name', 'vistara_categories', type_='unique')
    
    # Make client_id nullable
    op.alter_column('vistara_categories', 'client_id',
                    existing_type=sa.UUID(),
                    nullable=True)
    
    # Add new unique constraint for global categories (name only)
    op.create_unique_constraint('uq_vistara_categories_global_name', 'vistara_categories', ['name'])


def downgrade() -> None:
    """Revert changes - make client_id required again."""
    
    # Drop the global unique constraint
    op.drop_constraint('uq_vistara_categories_global_name', 'vistara_categories', type_='unique')
    
    # Make client_id non-nullable again (this will fail if there are NULL values)
    op.alter_column('vistara_categories', 'client_id',
                    existing_type=sa.UUID(),
                    nullable=False)
    
    # Recreate the original unique constraint
    op.create_unique_constraint('uq_vistara_categories_client_name', 'vistara_categories', ['client_id', 'name'])
