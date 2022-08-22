"""empty message

Revision ID: 50f90b4b414f
Revises: 2b26c46368ec
Create Date: 2022-08-17 12:45:02.621805

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

import app.util.sqlalchemy
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = '50f90b4b414f'
down_revision = '2b26c46368ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    create_seq("seq_Gebiedsprogrammas")
    op.create_table('Gebiedsprogrammas',
        sa.Column('ID', sa.Integer(), server_default=sa.text('NEXT VALUE FOR [seq_Gebiedsprogrammas]'), nullable=False),
        sa.Column('UUID', mssql.UNIQUEIDENTIFIER(), server_default=sa.text('(newid())'), nullable=False),
        sa.Column('Begin_Geldigheid', sa.DateTime(), nullable=False),
        sa.Column('Eind_Geldigheid', sa.DateTime(), nullable=False),
        sa.Column('Created_Date', sa.DateTime(), nullable=False),
        sa.Column('Modified_Date', sa.DateTime(), nullable=False),
        sa.Column('Status', sa.Unicode(length=50), nullable=False),
        sa.Column('Titel', sa.Unicode(length=150), nullable=False),
        sa.Column('Omschrijving', sa.Unicode(), nullable=True),
        sa.Column('Afbeelding', sa.Unicode(), nullable=True),
        sa.Column('Created_By', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('Modified_By', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.ForeignKeyConstraint(['Created_By'], ['Gebruikers.UUID'], name=op.f('FK_Gebiedsprogrammas_Created_By')),
        sa.ForeignKeyConstraint(['Modified_By'], ['Gebruikers.UUID'], name=op.f('FK_Gebiedsprogrammas_Modified_By')),
        sa.PrimaryKeyConstraint('UUID', name=op.f('PK_Gebiedsprogrammas'))
    )

    op.create_table('Maatregel_Gebiedsprogrammas',
        sa.Column('Maatregel_UUID', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('Gebiedsprogramma_UUID', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('Koppeling_Omschrijving', sa.String(collation='SQL_Latin1_General_CP1_CI_AS'), nullable=True),
        sa.ForeignKeyConstraint(['Gebiedsprogramma_UUID'], ['Gebiedsprogrammas.UUID'], name=op.f('FK_Maatregel_Gebiedsprogrammas_Gebiedsprogramma_UUID')),
        sa.ForeignKeyConstraint(['Maatregel_UUID'], ['Maatregelen.UUID'], name=op.f('FK_Maatregel_Gebiedsprogrammas_Maatregel_UUID')),
        sa.PrimaryKeyConstraint('Maatregel_UUID', 'Gebiedsprogramma_UUID', name=op.f('PK_Maatregel_Gebiedsprogrammas'))
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Maatregel_Gebiedsprogrammas')
    op.drop_table('Gebiedsprogrammas')
    drop_seq("seq_Gebiedsprogrammas")
    # ### end Alembic commands ###


def dialect_supports_sequences():
    return op._proxy.migration_context.dialect.supports_sequences


def dialect_supports_geometry_index():
    return op._proxy.migration_context.dialect.name == 'mssql'


def create_seq(name):
    if dialect_supports_sequences():
        op.execute(sa.schema.CreateSequence(sa.schema.Sequence(name)))


def drop_seq(name):
    if dialect_supports_sequences():
        op.execute(sa.schema.DropSequence(sa.schema.Sequence(name)))