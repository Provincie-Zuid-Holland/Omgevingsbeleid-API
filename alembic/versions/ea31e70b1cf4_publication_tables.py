"""publication tables

Revision ID: ea31e70b1cf4
Revises: 58ad22156b8b
Create Date: 2024-01-23 08:03:32.769512

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa
from app.extensions.werkingsgebieden.geometry import Geometry ## noqa

# revision identifiers, used by Alembic.
revision = "ea31e70b1cf4"
down_revision = "58ad22156b8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "Onderverdeling",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("ID", sa.Integer(), nullable=False),
        sa.Column("Onderverdeling", sa.String(), nullable=False),
        sa.Column("SHAPE", Geometry(), nullable=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("Werkingsgebied", sa.Unicode(length=265), nullable=False),
        sa.Column("UUID_Werkingsgebied", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Begin_Geldigheid", sa.DateTime(), nullable=False),
        sa.Column("Eind_Geldigheid", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_config",
        sa.Column("ID", sa.Integer(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Province_ID", sa.String(), nullable=False),
        sa.Column("Authority_ID", sa.String(255), nullable=False),
        sa.Column("Submitter_ID", sa.String(255), nullable=False),
        sa.Column("Jurisdiction", sa.String(), nullable=False),
        sa.Column("Subjects", sa.String(), nullable=False),
        sa.Column("dso_stop_version", sa.String(), nullable=False),
        sa.Column("dso_tpod_version", sa.String(), nullable=False),
        sa.Column("dso_bhkv_version", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.create_table(
        "publication_bills",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=True),
        sa.Column("Modified_Date", sa.DateTime(), nullable=True),
        sa.Column("Version_ID", sa.Integer(), nullable=False),
        sa.Column("Module_ID", sa.Integer(), nullable=False),
        sa.Column("Module_Status_ID", sa.Integer(), nullable=False),
        sa.Column("Council_Proposal_File", sa.String(), nullable=True),
        sa.Column("Effective_Date", sa.DateTime(), nullable=True),
        sa.Column("Announcement_Date", sa.DateTime(), nullable=True),
        sa.Column("Bill_Type", sa.Enum("Ontwerp", "Definitief"), nullable=True),
        sa.Column(
            "Document_Type",
            sa.Enum("Omgevingsvisie", "Omgevingsprogramma", "Omgevingsverordening"),
            nullable=True,
        ),
        sa.Column("Bill_Data", sa.JSON(), nullable=True),
        sa.Column("Procedure_Data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["Module_ID"],
            ["modules.Module_ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Module_Status_ID"],
            ["module_status_history.ID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
        sa.UniqueConstraint("Module_ID", "Document_Type", "Version_ID"),
    )
    op.create_table(
        "publication_packages",
        sa.Column("Bill_UUID", sa.Uuid(), nullable=False),
        sa.Column("Publication_Filename", sa.String(), nullable=True),
        sa.Column("Announcement_Date", sa.DateTime(), nullable=True),
        sa.Column("Province_ID", sa.String(), nullable=False),
        sa.Column("Submitter_ID", sa.String(255), nullable=False),
        sa.Column("Authority_ID", sa.String(255), nullable=False),
        sa.Column("Jurisdiction", sa.String(), nullable=False),
        sa.Column("Subjects", sa.String(), nullable=False),
        sa.Column("dso_stop_version", sa.String(), nullable=False),
        sa.Column("dso_tpod_version", sa.String(), nullable=False),
        sa.Column("dso_bhkv_version", sa.String(), nullable=False),
        sa.Column(
            "Package_Event_Type", sa.Enum("Validatie", "Publicatie", "Afbreken"), nullable=True
        ),
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=True),
        sa.Column("Modified_Date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["Bill_UUID"],
            ["publication_bills.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_dso_state_exports",
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("Export_Data", sa.JSON(), nullable=True),
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=True),
        sa.Column("Modified_Date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["Package_UUID"],
            ["publication_packages.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_ow_objects",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("OW_ID", sa.String(length=255), nullable=False),
        sa.Column(
            "IMOW_Type",
            sa.Enum(
                "regeltekst",
                "gebied",
                "gebiedengroep",
                "lijn",
                "lijnengroep",
                "punt",
                "puntengroep",
                "activiteit",
                "gebiedsaanwijzing",
                "omgevingswaarde",
                "omgevingsnorm",
                "pons",
                "kaart",
                "tekstdeel",
                "hoofdlijn",
                "divisie",
                "kaartlaag",
                "juridischeregel",
                "activiteitlocatieaanduiding",
                "normwaarde",
                "regelingsgebied",
                "ambtsgebied",
                "divisietekst",
            ),
            nullable=True,
        ),
        sa.Column("Procedure_Status", sa.Enum("Ontwerp", "Definitief"), nullable=True),
        sa.Column("Noemer", sa.String(), nullable=True),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("WID", sa.String(), nullable=True),
        sa.Column("Geo_UUID", sa.Integer(), nullable=True),
        sa.Column("Divisie_ref", sa.String(length=255), nullable=True),
        sa.Column("Bestuurlijke_grenzen_id", sa.String(), nullable=False),
        sa.Column("Domein", sa.String(), nullable=False),
        sa.Column("Geldig_Op", sa.String(), nullable=False),
        sa.Column("Ambtsgebied", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["Divisie_ref"],
            ["publication_ow_objects.OW_ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Geo_UUID"],
            ["modules.Module_ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Package_UUID"],
            ["publication_packages.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
        sa.UniqueConstraint("OW_ID"),
    )
    op.create_table(
        "publication_ow_association",
        sa.Column("OW_ID_1", sa.String(length=255), nullable=False),
        sa.Column("OW_ID_2", sa.String(length=255), nullable=False),
        sa.Column("Type", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["OW_ID_1"],
            ["publication_ow_objects.OW_ID"],
        ),
        sa.ForeignKeyConstraint(
            ["OW_ID_2"],
            ["publication_ow_objects.OW_ID"],
        ),
        sa.PrimaryKeyConstraint("OW_ID_1", "OW_ID_2"),
    )
    op.add_column(
        "Werkingsgebieden",
        sa.Column("SHAPE", Geometry(), nullable=True),
    )
    op.add_column("Werkingsgebieden", sa.Column("symbol", sa.Unicode(length=265), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("Werkingsgebieden", "symbol")
    op.drop_column("Werkingsgebieden", "SHAPE")
    op.drop_table("publication_ow_association")
    op.drop_table("publication_ow_objects")
    op.drop_table("publication_dso_state_exports")
    op.drop_table("publication_packages")
    op.drop_table("publication_bills")
    op.drop_table("publication_config")
    op.drop_table("Onderverdeling")
    # ### end Alembic commands ###
