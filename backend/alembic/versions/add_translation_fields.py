"""add translation fields to meeting and summary

Revision ID: add_translation_fields
Revises: 7e28e15cd9cf
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa

import pgvector

# revision identifiers, used by Alembic.
revision = 'add_translation_fields'
down_revision = '7e28e15cd9cf'
branch_labels = None
depends_on = None


def upgrade():
    # MEETING 테이블에 TRANSLATED_CONTENT 필드 추가
    op.add_column('MEETING', sa.Column('TRANSLATED_CONTENT', sa.TEXT(), nullable=True))
    
    # SUMMARY 테이블에 TRANSLATED_CONTENT 필드 추가
    op.add_column('SUMMARY', sa.Column('TRANSLATED_CONTENT', sa.TEXT(), nullable=True))


def downgrade():
    # SUMMARY 테이블에서 TRANSLATED_CONTENT 필드 제거
    op.drop_column('SUMMARY', 'TRANSLATED_CONTENT')
    
    # MEETING 테이블에서 TRANSLATED_CONTENT 필드 제거
    op.drop_column('MEETING', 'TRANSLATED_CONTENT')
