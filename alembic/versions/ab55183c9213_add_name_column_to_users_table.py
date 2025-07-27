"""Add name column to users table

Revision ID: ab55183c9213
Revises: f60d179bef43
Create Date: 2025-07-26 11:37:07.916331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab55183c9213'
down_revision: Union[str, Sequence[str], None] = 'f60d179bef43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
