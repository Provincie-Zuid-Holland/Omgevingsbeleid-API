"""Geo Input part 3

Revision ID: b61f0705fca0
Revises: 39a51a652bd7
Create Date: 2025-11-10 08:48:36.778845

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings  ## noqa

settings = Settings()


# revision identifiers, used by Alembic.
revision = 'b61f0705fca0'
down_revision = '39a51a652bd7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Area system upgrade
    op.add_column('areas', sa.Column('Source_Geometry_Index', sa.Unicode(length=10), nullable=True))
    op.add_column('areas', sa.Column('Source_Geometry_Hash', sa.Unicode(length=64), nullable=True))

    op.alter_column('areas', 'Source_Start_Validity', existing_type=sa.DATETIME(), nullable=True)
    op.alter_column('areas', 'Source_End_Validity', existing_type=sa.DATETIME(), nullable=True)
    op.alter_column('areas', 'Source_Modified_Date', existing_type=sa.DATETIME(), nullable=True)

    op.create_index(op.f('ix_areas_Source_Geometry_Index'), 'areas', ['Source_Geometry_Index'], unique=False)

    # Support Gebieden and Gebiedengroep_Code in Objects
    op.add_column('objects', sa.Column('Gebieden', sa.JSON(), nullable=True))
    op.add_column('objects', sa.Column('Gebiedengroep_Code', sa.Unicode(length=35), nullable=True))
    op.create_foreign_key('fk_o_os_gebiegengroep_code', 'objects', 'object_statics', ['Gebiedengroep_Code'], ['Code'])

    op.add_column('module_objects', sa.Column('Gebieden', sa.JSON(), nullable=True))
    op.add_column('module_objects', sa.Column('Gebiedengroep_Code', sa.Unicode(length=35), nullable=True))
    op.create_foreign_key('fk_mo_os_gebiegengroep_code', 'module_objects', 'object_statics', ['Gebiedengroep_Code'], ['Code'])
    
    # Source identifier system
    op.add_column('object_statics', sa.Column('Source_Identifier', sa.Unicode(length=255), nullable=True))

    # Backfill hashes & lookup from existing geometry ---
    op.execute("""
        UPDATE a
        SET
            Source_Geometry_Hash  = h.HashHex,
            Source_Geometry_Index = LEFT(h.HashHex, 10)
        FROM areas AS a
        CROSS APPLY (
            SELECT CONVERT(NVARCHAR(64), HASHBYTES('SHA2_256', a.[Shape].STAsBinary()), 2)
        ) AS h(HashHex)
        WHERE a.[Shape] IS NOT NULL;
    """)


def downgrade() -> None:
    op.drop_column('object_statics', 'Source_Identifier')

    op.drop_constraint('fk_mo_os_gebiegengroep_code', 'module_objects', type_='foreignkey')
    op.drop_column('module_objects', 'Gebiedengroep_Code')
    op.drop_column('module_objects', 'Gebieden')

    op.drop_constraint('fk_o_os_gebiegengroep_code', 'objects', type_='foreignkey')
    op.drop_column('objects', 'Gebiedengroep_Code')
    op.drop_column('objects', 'Gebieden')

    op.drop_index(op.f('ix_areas_Source_Geometry_Index'), table_name='areas')
    op.alter_column('areas', 'Source_Modified_Date', existing_type=sa.DATETIME(), nullable=False)
    op.alter_column('areas', 'Source_End_Validity', existing_type=sa.DATETIME(), nullable=False)
    op.alter_column('areas', 'Source_Start_Validity', existing_type=sa.DATETIME(), nullable=False)

    op.drop_column('areas', 'Source_Geometry_Hash')
    op.drop_column('areas', 'Source_Geometry_Index')
