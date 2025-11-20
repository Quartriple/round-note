"""rename USER to RN_USER

Revision ID: 811da328b9eb
Revises: 1cf54ddf96d3
Create Date: 2025-11-19 15:30:28.823005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '811da328b9eb'
down_revision: Union[str, Sequence[str], None] = '1cf54ddf96d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table from "USER" (with quotes) to RN_USER (without quotes)
    op.rename_table('"USER"', 'RN_USER')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename back to "USER" (with quotes)
    op.rename_table('RN_USER', '"USER"')
