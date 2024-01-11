"""Added foreign key and statics for hierarchy code

Revision ID: 58ad22156b8b
Revises: 626adccffe91
Create Date: 2024-01-06 16:12:18.209291

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import settings  ## noqa 



# revision identifiers, used by Alembic.
revision = '58ad22156b8b'
down_revision = '626adccffe91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'module_objects', 'object_statics', ['Hierarchy_Code'], ['Code'])
    op.create_foreign_key(None, 'objects', 'object_statics', ['Hierarchy_Code'], ['Code'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'objects', type_='foreignkey')
    op.drop_constraint(None, 'module_objects', type_='foreignkey')
    # ### end Alembic commands ###