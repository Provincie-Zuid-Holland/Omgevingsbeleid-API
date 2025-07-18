""" Added input GEO tables for Werkingsgebieden and Onderverdeling

Revision ID: d9ad1aa2d0ce
Revises: bd48c9bf106d
Create Date: 2025-03-04 12:46:55.668737

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.db.geometry import Geometry


# revision identifiers, used by Alembic.
revision = 'd9ad1aa2d0ce'
down_revision = 'bd48c9bf106d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Input_GEO_Werkingsgebieden',
        sa.Column('UUID', sa.Uuid(), nullable=False),
        sa.Column('Title', sa.String(), nullable=False),
        sa.Column('Created_Date', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('UUID')
    )
    op.create_table('Input_GEO_Onderverdeling',
        sa.Column('UUID', sa.Uuid(), nullable=False),
        sa.Column('Title', sa.String(), nullable=False),
        sa.Column('Created_Date', sa.DateTime(), nullable=False),
        sa.Column('Geometry', Geometry(), nullable=True),
        sa.Column('Geometry_Hash', sa.Unicode(length=64), nullable=False),
        sa.Column('GML', sa.Unicode(), nullable=True),
        sa.Column('Werkingsgebied_UUID', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['Werkingsgebied_UUID'], ['Input_GEO_Werkingsgebieden.UUID'], ),
        sa.PrimaryKeyConstraint('UUID')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Input_GEO_Onderverdeling')
    op.drop_table('Input_GEO_Werkingsgebieden')
    # ### end Alembic commands ###
