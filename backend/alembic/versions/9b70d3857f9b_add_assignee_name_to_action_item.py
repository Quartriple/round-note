"""add_assignee_name_to_action_item

Revision ID: 9b70d3857f9b
Revises: 8ccd0f017058
Create Date: 2025-11-24 02:47:19.535972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b70d3857f9b'
down_revision: Union[str, Sequence[str], None] = '8ccd0f017058'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ACTION_ITEM', sa.Column('ASSIGNEE_NAME', sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ACTION_ITEM', 'ASSIGNEE_NAME')
