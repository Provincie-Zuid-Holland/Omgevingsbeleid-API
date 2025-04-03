""" Sync werkingsgebieden with PROD

Revision ID: 8455fd1c7d2d
Revises: 52aa3b967a4b
Create Date: 2024-08-06 12:24:32.461186

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings

settings = Settings()


# revision identifiers, used by Alembic.
revision = '8455fd1c7d2d'
down_revision = '52aa3b967a4b'
branch_labels = None
depends_on = None

# Werkingsgebied table is only touched on local dev environments
def upgrade() -> None:
    if not settings.LOCAL_DEVELOPMENT_MODE:
        return

    op.add_column('Werkingsgebieden', sa.Column('GML', sa.Unicode(), nullable=True))


def downgrade() -> None:
    if not settings.LOCAL_DEVELOPMENT_MODE:
        return

    op.drop_column('Werkingsgebieden', 'GML')
