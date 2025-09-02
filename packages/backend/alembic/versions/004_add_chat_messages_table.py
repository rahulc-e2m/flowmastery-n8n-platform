"""Add chat messages table

Revision ID: 004_add_chat_messages_table
Revises: 003_add_chatbots_table
Create Date: 2025-09-02 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_chat_messages_table'
down_revision = '003_add_chatbots_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('chatbot_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('bot_response', sa.Text(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'], unique=False)
    op.create_index('ix_chat_messages_conversation_id', 'chat_messages', ['conversation_id'], unique=False)
    op.create_index('ix_chat_messages_chatbot_id', 'chat_messages', ['chatbot_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_chat_messages_chatbot_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_conversation_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_id', table_name='chat_messages')
    
    # Drop table
    op.drop_table('chat_messages')