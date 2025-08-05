"""Add ratings table

Revision ID: cd4354da8961
Revises: b476b1ef9756
Create Date: 2025-08-05 15:15:29.407188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd4354da8961'
down_revision: Union[str, None] = 'b476b1ef9756'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ratings',
        sa.Column('rating_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.user_id', ondelete='CASCADE')),
        sa.Column('rating', sa.Float),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('version', sa.Text)
    )
    pass


def downgrade() -> None:
    op.drop_table('ratings')
    pass
