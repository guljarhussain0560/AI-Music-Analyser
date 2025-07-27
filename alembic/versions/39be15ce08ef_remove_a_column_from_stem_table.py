"""remove a column from stem table

Revision ID: 39be15ce08ef
Revises: af9d32e501f4
Create Date: 2025-07-26 11:42:59.419855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39be15ce08ef'
down_revision: Union[str, Sequence[str], None] = 'af9d32e501f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
