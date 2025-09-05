"""rename_dependencies_table_to_guides

Revision ID: 53f4cebff7c6
Revises: 89e72050d105
Create Date: 2025-09-05 08:10:54.332794

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53f4cebff7c6'
down_revision = '89e72050d105'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the table from dependencies to guides
    op.rename_table('dependencies', 'guides')


def downgrade() -> None:
    # Rename the table back from guides to dependencies
    op.rename_table('guides', 'dependencies')
