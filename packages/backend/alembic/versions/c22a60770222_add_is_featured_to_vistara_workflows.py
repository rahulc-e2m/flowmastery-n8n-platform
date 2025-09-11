"""add_is_featured_to_vistara_workflows

Revision ID: c22a60770222
Revises: 90f571f0297b
Create Date: 2025-09-08 11:44:49.444953

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c22a60770222'
down_revision = '90f571f0297b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_featured column to vistara_workflows table
    op.add_column('vistara_workflows', 
                  sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_featured column from vistara_workflows table
    op.drop_column('vistara_workflows', 'is_featured')
