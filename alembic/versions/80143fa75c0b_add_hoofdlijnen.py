"""add hoofdlijnen

Revision ID: 80143fa75c0b
Revises: 826c32155e0a
Create Date: 2026-06-15 12:57:20.097495

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings  ## noqa

settings = Settings()



# revision identifiers, used by Alembic.
revision = '80143fa75c0b'
down_revision = '826c32155e0a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("module_objects", sa.Column("Hoofdlijn_Type", sa.Unicode(), nullable=True))
    op.add_column("objects", sa.Column("Hoofdlijn_Type", sa.Unicode(), nullable=True))
    op.add_column("module_objects", sa.Column("Hoofdlijnen", sa.JSON(), nullable=True))
    op.add_column("objects", sa.Column("Hoofdlijnen", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("objects", "Hoofdlijn_Type")
    op.drop_column("module_objects", "Hoofdlijn_Type")
    op.drop_column("objects", "Hoofdlijnen")
    op.drop_column("module_objects", "Hoofdlijnen")
