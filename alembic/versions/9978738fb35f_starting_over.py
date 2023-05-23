"""Starting over

Revision ID: 9978738fb35f
Revises: 
Create Date: 2023-05-22 14:43:07.010191

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import settings  ## noqa 



# revision identifiers, used by Alembic.
revision = '9978738fb35f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Gebruikers',
    sa.Column('Gebruikersnaam', sa.String(), nullable=True),
    sa.Column('Email', sa.String(length=256), nullable=False),
    sa.Column('Rol', sa.String(), nullable=True),
    sa.Column('Status', sa.String(), nullable=True),
    sa.Column('Wachtwoord', sa.String(), nullable=True),
    sa.Column('UUID', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('UUID'),
    sa.UniqueConstraint('Email')
    )
    op.create_table('Werkingsgebieden',
    sa.Column('UUID', sa.Uuid(), nullable=False),
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=False),
    sa.Column('Modified_Date', sa.DateTime(), nullable=False),
    sa.Column('Werkingsgebied', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('UUID')
    )
    op.create_table('assets',
    sa.Column('UUID', sa.Uuid(), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=False),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Lookup', sa.String(length=10), nullable=False),
    sa.Column('Hash', sa.String(length=64), nullable=False),
    sa.Column('Meta', sa.String(), nullable=False),
    sa.Column('Content', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.PrimaryKeyConstraint('UUID')
    )
    op.create_index(op.f('ix_assets_Lookup'), 'assets', ['Lookup'], unique=False)
    op.create_table('modules',
    sa.Column('Module_ID', sa.Integer(), nullable=False),
    sa.Column('Activated', sa.Boolean(), nullable=False),
    sa.Column('Closed', sa.Boolean(), nullable=False),
    sa.Column('Successful', sa.Boolean(), nullable=False),
    sa.Column('Temporary_Locked', sa.Boolean(), nullable=False),
    sa.Column('Title', sa.String(), nullable=False),
    sa.Column('Description', sa.String(), nullable=False),
    sa.Column('Module_Manager_1_UUID', sa.Uuid(), nullable=True),
    sa.Column('Module_Manager_2_UUID', sa.Uuid(), nullable=True),
    sa.Column('Created_Date', sa.DateTime(), nullable=True),
    sa.Column('Modified_Date', sa.DateTime(), nullable=True),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Module_Manager_1_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Module_Manager_2_UUID'], ['Gebruikers.UUID'], ),
    sa.PrimaryKeyConstraint('Module_ID')
    )
    op.create_table('object_statics',
    sa.Column('Object_Type', sa.String(length=25), nullable=False),
    sa.Column('Object_ID', sa.Integer(), nullable=False),
    sa.Column('Code', sa.String(length=35), nullable=False),
    sa.Column('Owner_1_UUID', sa.Uuid(), nullable=True),
    sa.Column('Owner_2_UUID', sa.Uuid(), nullable=True),
    sa.Column('Portfolio_Holder_1_UUID', sa.Uuid(), nullable=True),
    sa.Column('Portfolio_Holder_2_UUID', sa.Uuid(), nullable=True),
    sa.Column('Client_1_UUID', sa.Uuid(), nullable=True),
    sa.Column('Cached_Title', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['Client_1_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Owner_1_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Owner_2_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Portfolio_Holder_1_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Portfolio_Holder_2_UUID'], ['Gebruikers.UUID'], ),
    sa.PrimaryKeyConstraint('Code')
    )
    op.create_table('acknowledged_relations',
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
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['From_Acknowledged_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['From_Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Requested_By_Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['To_Acknowledged_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['To_Code'], ['object_statics.Code'], ),
    sa.PrimaryKeyConstraint('Version', 'From_Code', 'To_Code')
    )
    op.create_table('module_object_context',
    sa.Column('Module_ID', sa.Integer(), nullable=False),
    sa.Column('Object_Type', sa.String(length=25), nullable=False),
    sa.Column('Object_ID', sa.Integer(), nullable=False),
    sa.Column('Code', sa.String(length=35), nullable=False),
    sa.Column('Original_Adjust_On', sa.Uuid(), nullable=True),
    sa.Column('Hidden', sa.Boolean(), nullable=False),
    sa.Column('Action', sa.String(), nullable=False),
    sa.Column('Explanation', sa.String(), nullable=False),
    sa.Column('Conclusion', sa.String(), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=True),
    sa.Column('Modified_Date', sa.DateTime(), nullable=True),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Module_ID'], ['modules.Module_ID'], ),
    sa.PrimaryKeyConstraint('Module_ID', 'Code')
    )
    op.create_table('module_status_history',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Module_ID', sa.Integer(), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=False),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Status', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Module_ID'], ['modules.Module_ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('objects',
    sa.Column('UUID', sa.Uuid(), nullable=False),
    sa.Column('Code', sa.String(length=35), nullable=False),
    sa.Column('Object_ID', sa.Integer(), nullable=False),
    sa.Column('Object_Type', sa.String(length=25), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=False),
    sa.Column('Modified_Date', sa.DateTime(), nullable=False),
    sa.Column('Adjust_On', sa.Uuid(), nullable=True),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Start_Validity', sa.String(), nullable=True),
    sa.Column('End_Validity', sa.String(), nullable=True),
    sa.Column('Title', sa.String(), nullable=True),
    sa.Column('Description', sa.String(), nullable=True),
    sa.Column('Description_Choice', sa.String(), nullable=True),
    sa.Column('Description_Operation', sa.String(), nullable=True),
    sa.Column('Accomplish', sa.String(), nullable=True),
    sa.Column('Effect', sa.String(), nullable=True),
    sa.Column('Role', sa.String(), nullable=True),
    sa.Column('Provincial_Interest', sa.String(), nullable=True),
    sa.Column('Cause', sa.String(), nullable=True),
    sa.Column('Consideration', sa.String(), nullable=True),
    sa.Column('Decision_Number', sa.String(), nullable=True),
    sa.Column('Explanation', sa.String(), nullable=True),
    sa.Column('Explanation_Raw', sa.String(), nullable=True),
    sa.Column('Weblink', sa.String(), nullable=True),
    sa.Column('Tags', sa.String(), nullable=True),
    sa.Column('IDMS_Link', sa.String(), nullable=True),
    sa.Column('Gebied_UUID', sa.Uuid(), nullable=True),
    sa.Column('Gebied_Duiding', sa.String(), nullable=True),
    sa.Column('Image', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Gebied_UUID'], ['Werkingsgebieden.UUID'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.PrimaryKeyConstraint('UUID')
    )
    op.create_table('relations',
    sa.Column('From_Code', sa.String(length=35), nullable=False),
    sa.Column('To_Code', sa.String(length=35), nullable=False),
    sa.Column('Description', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['From_Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['To_Code'], ['object_statics.Code'], ),
    sa.PrimaryKeyConstraint('From_Code', 'To_Code')
    )
    op.create_table('module_objects',
    sa.Column('Module_ID', sa.Integer(), nullable=False),
    sa.Column('UUID', sa.Uuid(), nullable=False),
    sa.Column('Code', sa.String(length=35), nullable=False),
    sa.Column('Deleted', sa.Boolean(), nullable=False),
    sa.Column('Object_ID', sa.Integer(), nullable=False),
    sa.Column('Object_Type', sa.String(length=25), nullable=False),
    sa.Column('Created_Date', sa.DateTime(), nullable=False),
    sa.Column('Modified_Date', sa.DateTime(), nullable=False),
    sa.Column('Adjust_On', sa.Uuid(), nullable=True),
    sa.Column('Created_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Modified_By_UUID', sa.Uuid(), nullable=False),
    sa.Column('Start_Validity', sa.String(), nullable=True),
    sa.Column('End_Validity', sa.String(), nullable=True),
    sa.Column('Title', sa.String(), nullable=True),
    sa.Column('Description', sa.String(), nullable=True),
    sa.Column('Description_Choice', sa.String(), nullable=True),
    sa.Column('Description_Operation', sa.String(), nullable=True),
    sa.Column('Accomplish', sa.String(), nullable=True),
    sa.Column('Effect', sa.String(), nullable=True),
    sa.Column('Role', sa.String(), nullable=True),
    sa.Column('Provincial_Interest', sa.String(), nullable=True),
    sa.Column('Cause', sa.String(), nullable=True),
    sa.Column('Consideration', sa.String(), nullable=True),
    sa.Column('Decision_Number', sa.String(), nullable=True),
    sa.Column('Explanation', sa.String(), nullable=True),
    sa.Column('Explanation_Raw', sa.String(), nullable=True),
    sa.Column('Weblink', sa.String(), nullable=True),
    sa.Column('Tags', sa.String(), nullable=True),
    sa.Column('IDMS_Link', sa.String(), nullable=True),
    sa.Column('Gebied_UUID', sa.Uuid(), nullable=True),
    sa.Column('Gebied_Duiding', sa.String(), nullable=True),
    sa.Column('Image', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['Code'], ['object_statics.Code'], ),
    sa.ForeignKeyConstraint(['Created_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Gebied_UUID'], ['Werkingsgebieden.UUID'], ),
    sa.ForeignKeyConstraint(['Modified_By_UUID'], ['Gebruikers.UUID'], ),
    sa.ForeignKeyConstraint(['Module_ID', 'Code'], ['module_object_context.Module_ID', 'module_object_context.Code'], ),
    sa.ForeignKeyConstraint(['Module_ID'], ['modules.Module_ID'], ),
    sa.PrimaryKeyConstraint('UUID')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('module_objects')
    op.drop_table('relations')
    op.drop_table('objects')
    op.drop_table('module_status_history')
    op.drop_table('module_object_context')
    op.drop_table('acknowledged_relations')
    op.drop_table('object_statics')
    op.drop_table('modules')
    op.drop_index(op.f('ix_assets_Lookup'), table_name='assets')
    op.drop_table('assets')
    op.drop_table('Werkingsgebieden')
    op.drop_table('Gebruikers')
    # ### end Alembic commands ###
