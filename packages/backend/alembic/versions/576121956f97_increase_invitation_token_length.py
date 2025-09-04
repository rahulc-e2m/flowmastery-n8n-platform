"""increase_invitation_token_length

Revision ID: 576121956f97
Revises: 9087571cea63
Create Date: 2025-09-04 06:41:22.575202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '576121956f97'
down_revision = '9087571cea63'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Increase invitation token column length from 255 to 500 characters
    op.alter_column('invitations', 'token',
                    existing_type=sa.String(255),
                    type_=sa.String(500),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert invitation token column length back to 255 characters
    op.alter_column('invitations', 'token',
                    existing_type=sa.String(500),
                    type_=sa.String(255),
                    existing_nullable=False)