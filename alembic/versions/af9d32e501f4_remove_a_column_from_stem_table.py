"""remove a column from stem table

Revision ID: af9d32e501f4
Revises: ab55183c9213
Create Date: 2025-07-26 11:39:35.691916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af9d32e501f4'
down_revision: Union[str, Sequence[str], None] = 'ab55183c9213'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('splits', 'stem_type')


def downgrade() -> None:
    """Downgrade schema."""
    # NOTE: You must adjust the column type (sa.String, sa.Integer, etc.)
    # to match the original 'sten_type' column's definition.
    op.add_column('splits', sa.Column('stem_type', sa.String(), nullable=True))
