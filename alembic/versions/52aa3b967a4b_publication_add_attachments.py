""" Publication add attachments

Revision ID: 52aa3b967a4b
Revises: 43f8adfab60c
Create Date: 2024-05-05 15:26:31.306739

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
revision = '52aa3b967a4b'
down_revision = '43f8adfab60c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('publication_storage_files',
        sa.Column('UUID', sa.Uuid(), nullable=False),
        sa.Column('Lookup', sa.Unicode(length=10), nullable=False),
        sa.Column('Checksum', sa.String(length=64), nullable=False),
        sa.Column('Filename', sa.Unicode(length=255), nullable=False),
        sa.Column('Content_Type', sa.Unicode(length=64), nullable=False),
        sa.Column('Size', sa.Integer(), nullable=False),
        sa.Column('Binary', sa.LargeBinary(), nullable=False),
        sa.Column('Created_Date', sa.DateTime(), nullable=False),
        sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
        sa.PrimaryKeyConstraint('UUID')
    )
    op.create_index(op.f('ix_publication_storage_files_Lookup'), 'publication_storage_files', ['Lookup'], unique=False)
    op.create_table('publication_version_attachments',
        sa.Column('ID', sa.Integer(), nullable=False),
        sa.Column('Publication_Version_UUID', sa.Uuid(), nullable=False),
        sa.Column('File_UUID', sa.Uuid(), nullable=False),
        sa.Column('Filename', sa.Unicode(length=255), nullable=False),
        sa.Column('Title', sa.Unicode(length=255), nullable=False),
        sa.Column('Created_Date', sa.DateTime(), nullable=False),
        sa.Column('Modified_Date', sa.DateTime(), nullable=False),
        sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
        sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
        sa.ForeignKeyConstraint(['File_UUID'], ['publication_storage_files.UUID'], ),
        sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
        sa.ForeignKeyConstraint(['Publication_Version_UUID'], ['publication_versions.UUID'], ),
        sa.PrimaryKeyConstraint('ID'),
        sa.UniqueConstraint('Publication_Version_UUID', 'File_UUID', name='uix_publication_version_file')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('publication_version_attachments')
    op.drop_index(op.f('ix_publication_storage_files_Lookup'), table_name='publication_storage_files')
    op.drop_table('publication_storage_files')
    # ### end Alembic commands ###