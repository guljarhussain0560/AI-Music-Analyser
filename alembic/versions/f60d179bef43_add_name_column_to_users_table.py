"""Add name column to users table

Revision ID: f60d179bef43
Revises: 
Create Date: 2025-07-25 01:20:51.834962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f60d179bef43'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add 'name' column to 'users' table."""
    op.add_column('users', sa.Column('name', sa.String(), nullable=True))

def downgrade() -> None:
    """Downgrade schema: remove 'name' column from 'users' table."""
    op.drop_column('users', 'name')
