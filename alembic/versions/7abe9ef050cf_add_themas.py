"""add themas

Revision ID: 7abe9ef050cf
Revises: 826c32155e0a
Create Date: 2026-06-09 14:29:57.486673

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings  ## noqa

settings = Settings()



# revision identifiers, used by Alembic.
revision = '7abe9ef050cf'
down_revision = '826c32155e0a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('module_objects', sa.Column('Themas', sa.JSON(), nullable=True))
    op.add_column('objects', sa.Column('Themas', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('objects', 'Themas')
    op.drop_column('module_objects', 'Themas')
