"""add gebiedsaanwijzingen

Revision ID: a4c647a3757e
Revises: 5f6dde59d68e
Create Date: 2026-03-09 12:39:35.992745

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings  ## noqa

settings = Settings()



# revision identifiers, used by Alembic.
revision = 'a4c647a3757e'
down_revision = '5f6dde59d68e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('module_objects', sa.Column('Ref_Type', sa.Unicode(), nullable=True))
    op.add_column('objects', sa.Column('Ref_Type', sa.Unicode(), nullable=True))
    op.add_column('module_objects', sa.Column('Ref_Group', sa.Unicode(), nullable=True))
    op.add_column('objects', sa.Column('Ref_Group', sa.Unicode(), nullable=True))
    op.add_column('module_objects', sa.Column('Target_Codes', sa.JSON(), nullable=True))
    op.add_column('objects', sa.Column('Target_Codes', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('objects', 'Ref_Type')
    op.drop_column('module_objects', 'Ref_Type')
    op.drop_column('objects', 'Ref_Group')
    op.drop_column('module_objects', 'Ref_Group')
    op.drop_column('objects', 'Target_Codes')
    op.drop_column('module_objects', 'Target_Codes')
