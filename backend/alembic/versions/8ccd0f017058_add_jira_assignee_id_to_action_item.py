"""add_jira_assignee_id_to_action_item

Revision ID: 8ccd0f017058
Revises: 7923fc9c0290
Create Date: 2025-11-24 02:35:06.868116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = '8ccd0f017058'
down_revision: Union[str, Sequence[str], None] = '7923fc9c0290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ACTION_ITEM', sa.Column('JIRA_ASSIGNEE_ID', sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ACTION_ITEM', 'JIRA_ASSIGNEE_ID')
