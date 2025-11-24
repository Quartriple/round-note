"""add_user_integration_setting_and_jira_project_key

Revision ID: 7923fc9c0290
Revises: add_translation_fields
Create Date: 2025-11-24 09:26:23.724025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import pgvector

# revision identifiers, used by Alembic.
revision: str = '7923fc9c0290'
down_revision: Union[str, Sequence[str], None] = 'add_translation_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. USER_INTEGRATION_SETTING 테이블 생성
    op.create_table(
        'USER_INTEGRATION_SETTING',
        sa.Column('INTEGRATION_ID', sa.TEXT(), nullable=False),
        sa.Column('USER_ID', sa.TEXT(), nullable=False),
        sa.Column('PLATFORM', sa.TEXT(), nullable=False),
        sa.Column('CONFIG', JSONB(), nullable=False),
        sa.Column('IS_ACTIVE', sa.TEXT(), nullable=False, server_default='Y'),
        sa.Column('CREATED_DT', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('UPDATED_DT', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['USER_ID'], ['RN_USER.USER_ID'], ),
        sa.PrimaryKeyConstraint('INTEGRATION_ID'),
        sa.CheckConstraint('"IS_ACTIVE" IN (\'Y\', \'N\')', name='ck_integration_is_active'),
        sa.CheckConstraint('"PLATFORM" IN (\'jira\', \'notion\', \'google_calendar\')', name='ck_integration_platform')
    )
    
    # 2. MEETING 테이블에 JIRA_PROJECT_KEY 컬럼 추가
    op.add_column('MEETING', sa.Column('JIRA_PROJECT_KEY', sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 2. MEETING 테이블에서 JIRA_PROJECT_KEY 컬럼 제거
    op.drop_column('MEETING', 'JIRA_PROJECT_KEY')
    
    # 1. USER_INTEGRATION_SETTING 테이블 삭제
    op.drop_table('USER_INTEGRATION_SETTING')
