""" Publication state V2

Revision ID: 348162e768ec
Revises: 8455fd1c7d2d
Create Date: 2024-08-06 12:37:27.446619

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
revision = '348162e768ec'
down_revision = '8455fd1c7d2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('publication_area_of_jurisdictions', sa.Column('Title', sa.Unicode(), server_default='', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('publication_area_of_jurisdictions', 'Title')
    # ### end Alembic commands ###
