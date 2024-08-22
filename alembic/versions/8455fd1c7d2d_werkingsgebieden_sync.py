""" Sync werkingsgebieden with PROD

Revision ID: 8455fd1c7d2d
Revises: 52aa3b967a4b
Create Date: 2024-08-06 12:24:32.461186

"""
from alembic import op
import sqlalchemy as sa
from app.extensions.source_werkingsgebieden import geometry  ## noqa
from app.extensions.source_werkingsgebieden.geometry import Geometry  ## noqa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import settings  ## noqa 



# revision identifiers, used by Alembic.
revision = '8455fd1c7d2d'
down_revision = '52aa3b967a4b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Werkingsgebieden', sa.Column('GML', sa.Unicode(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Werkingsgebieden', 'GML')
    # ### end Alembic commands ###