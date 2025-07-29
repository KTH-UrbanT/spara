"""Initilization

Revision ID: b476b1ef9756
Revises: 
Create Date: 2025-07-29 14:38:31.266011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b476b1ef9756'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(50)),
        sa.Column('email', sa.String(100)),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_logged_in', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'sessions',
        sa.Column('session_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.user_id', ondelete='CASCADE')),
        sa.Column('session_token', sa.String(255), unique=True, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_accessed', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'messages',
        sa.Column('message_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer, sa.ForeignKey('sessions.session_id', ondelete='CASCADE')),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('sent_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    pass


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('users')
    pass
