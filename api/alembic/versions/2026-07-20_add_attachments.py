"""add attachments

Revision ID: add_attachments_id
Revises: 2026-07-20_add_unread_id
Create Date: 2026-07-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '244ba73ab0df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('attachment',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('content_type', sa.String(length=128), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('reply_id', sa.Integer(), nullable=True),
        sa.Column('general_chat_message_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['general_chat_message_id'], ['general_chat_message.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reply_id'], ['reply.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ticket_id'], ['ticket.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('attachment')
