"""empty message

Revision ID: eb6126c067be
Revises: 2dbf768b0401
Create Date: 2023-05-15 16:39:57.125950

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import settings  ## noqa 



# revision identifiers, used by Alembic.
revision = 'eb6126c067be'
down_revision = '2dbf768b0401'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('acknowledged_relations')
    op.create_table(
        'acknowledged_relations',
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Requested_By_Code', sa.String(length=35), nullable=False),
        sa.Column('From_Code', sa.String(length=35), nullable=False),
        sa.Column('From_Acknowledged', sa.DateTime(), nullable=True),
        sa.Column('From_Acknowledged_By_UUID', sa.Uuid(), nullable=True),
        sa.Column('From_Explanation', sa.String(), nullable=False),
        sa.Column('To_Code', sa.String(length=35), nullable=False),
        sa.Column('To_Acknowledged', sa.DateTime(), nullable=True),
        sa.Column('To_Acknowledged_By_UUID', sa.Uuid(), nullable=True),
        sa.Column('To_Explanation', sa.String(), nullable=False),
        sa.Column('Denied', sa.DateTime(), nullable=True),
        sa.Column('Deleted_At', sa.DateTime(), nullable=True),
        sa.Column('Created_Date', sa.DateTime(), nullable=True),
        sa.Column('Modified_Date', sa.DateTime(), nullable=True),
        sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
        sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID']),
        sa.ForeignKeyConstraint(['From_Acknowledged_By_UUID'], ['Gebruikers.UUID']),
        sa.ForeignKeyConstraint(['From_Code'], ['object_statics.Code']),
        sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID']),
        sa.ForeignKeyConstraint(['Requested_By_Code'], ['object_statics.Code']),
        sa.ForeignKeyConstraint(['To_Acknowledged_By_UUID'], ['Gebruikers.UUID']),
        sa.ForeignKeyConstraint(['To_Code'], ['object_statics.Code']),
        sa.PrimaryKeyConstraint('Version', 'Requested_By_Code', 'From_Code', 'To_Code')
    )


def downgrade() -> None:
    op.drop_table('acknowledged_relations')
    op.create_table('acknowledged_relations',
    sa.Column('Requested_By_Code', sa.String(length=35), nullable=False),
    sa.Column('From_Code', sa.String(length=35), nullable=False),
    sa.Column('From_Acknowledged', sa.DateTime(), nullable=True),
    sa.Column('From_Acknowledged_By_UUID', sa.Uuid(), nullable=True),
    sa.Column('From_Explanation', sa.String(), nullable=False),
    sa.Column('To_Code', sa.String(length=35), nullable=False),
    sa.Column('To_Acknowledged', sa.DateTime(), nullable=True),
    sa.Column('To_Acknowledged_By_UUID', sa.Uuid(), nullable=True),
    sa.Column('To_Explanation', sa.String(), nullable=False),
    sa.Column('Denied', sa.DateTime(), nullable=True),
    sa.Column('Deleted_At', sa.DateTime(), nullable=True),
    sa.Column('Created_Date', sa.DateTime(), nullable=True),
    sa.Column('Modified_Date', sa.DateTime(), nullable=True),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['From_Acknowledged_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['From_Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Requested_By_Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['To_Acknowledged_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['To_Code'], ['object_statics.Code'], ),
    sa.PrimaryKeyConstraint('Requested_By_Code', 'From_Code', 'To_Code')
    )
