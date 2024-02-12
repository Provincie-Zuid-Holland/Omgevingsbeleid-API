"""Adding Publications

Revision ID: da2cc1de90bd
Revises: 00c1d7bd6337
Create Date: 2024-02-08 15:37:17.514599

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa


# revision identifiers, used by Alembic.
revision = "da2cc1de90bd"
down_revision = "00c1d7bd6337"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "publication_config",
        sa.Column("ID", sa.Integer(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Province_ID", sa.Unicode(length=255), nullable=False),
        sa.Column("Authority_ID", sa.Unicode(length=255), nullable=False),
        sa.Column("Submitter_ID", sa.Unicode(length=255), nullable=False),
        sa.Column("Jurisdiction", sa.Unicode(length=255), nullable=False),
        sa.Column("Subjects", sa.Unicode(length=255), nullable=False),
        sa.Column("Governing_Body_Type", sa.Unicode(length=255), nullable=False),
        sa.Column("Act_Componentname", sa.Unicode(length=255), nullable=False),
        sa.Column("DSO_STOP_VERSION", sa.Unicode(length=255), nullable=False),
        sa.Column("DSO_TPOD_VERSION", sa.Unicode(length=255), nullable=False),
        sa.Column("DSO_BHKV_VERSION", sa.Unicode(length=255), nullable=False),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.create_table(
        "publication_frbr",
        sa.Column("ID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("bill_work_country", sa.Unicode(length=255), nullable=False),
        sa.Column("bill_work_date", sa.Unicode(length=255), nullable=False),
        sa.Column("bill_work_misc", sa.Unicode(length=255), nullable=False),
        sa.Column("bill_expression_lang", sa.Unicode(length=255), nullable=False),
        sa.Column("bill_expression_date", sa.Date(), nullable=False),
        sa.Column("bill_expression_version", sa.Unicode(length=255), nullable=False),
        sa.Column("bill_expression_misc", sa.Unicode(length=255), nullable=True),
        sa.Column("act_work_country", sa.Unicode(length=255), nullable=False),
        sa.Column("act_work_date", sa.Unicode(length=255), nullable=False),
        sa.Column("act_work_misc", sa.Unicode(length=255), nullable=False),
        sa.Column("act_expression_lang", sa.Unicode(length=255), nullable=False),
        sa.Column("act_expression_date", sa.Date(), nullable=False),
        sa.Column("act_expression_version", sa.Unicode(length=255), nullable=False),
        sa.Column("act_expression_misc", sa.Unicode(length=255), nullable=True),
        sa.PrimaryKeyConstraint("ID"),
        sa.UniqueConstraint("act_work_misc", "act_expression_version", name="act_unique_constraint"),
        sa.UniqueConstraint("bill_work_misc", "bill_expression_version", name="bill_unique_constraint"),
    )
    op.create_table(
        "publications",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Created_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Module_ID", sa.Integer(), nullable=False),
        sa.Column("Template_ID", sa.Integer(), nullable=True),
        sa.Column("Work_ID", sa.Integer(), nullable=False),
        sa.Column(
            "Document_Type", sa.Enum("Omgevingsvisie", "Omgevingsprogramma", "Omgevingsverordening"), nullable=True
        ),
        sa.Column("Official_Title", sa.Unicode(), nullable=False),
        sa.Column("Regulation_Title", sa.Unicode(), nullable=False),
        sa.ForeignKeyConstraint(
            ["Created_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Modified_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Module_ID"],
            ["modules.Module_ID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
        sa.UniqueConstraint("Document_Type", "Work_ID", name="uq_publications_document_work"),
    )
    op.create_table(
        "publication_bills",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Created_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Publication_UUID", sa.Uuid(), nullable=False),
        sa.Column("Module_Status_ID", sa.Integer(), nullable=False),
        sa.Column("Procedure_Type", sa.Enum("Ontwerp", "Definitief"), nullable=False),
        sa.Column("Bill_Data", sa.JSON(), nullable=True),
        sa.Column("Procedure_Data", sa.JSON(), nullable=True),
        sa.Column("Version_ID", sa.Integer(), nullable=False),
        sa.Column("Is_Official", sa.Boolean(), nullable=False),
        sa.Column("Effective_Date", sa.Date(), nullable=True),
        sa.Column("Announcement_Date", sa.Date(), nullable=True),
        sa.Column("PZH_Bill_Identifier", sa.Unicode(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["Created_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Modified_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Module_Status_ID"],
            ["module_status_history.ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Publication_UUID"],
            ["publications.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_packages",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Created_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Bill_UUID", sa.Uuid(), nullable=False),
        sa.Column("Config_ID", sa.Integer(), nullable=False),
        sa.Column("FRBR_ID", sa.Integer(), nullable=False),
        sa.Column("Package_Event_Type", sa.Enum("Validatie", "Publicatie", "Afbreken"), nullable=False),
        sa.Column("Publication_Filename", sa.Unicode(length=255), nullable=True),
        sa.Column("Announcement_Date", sa.Date(), nullable=False),
        sa.Column("ZIP_File_Name", sa.Unicode(), nullable=True),
        sa.Column("ZIP_File_Binary", sa.LargeBinary(), nullable=True),
        sa.Column("ZIP_File_Checksum", sa.Unicode(length=64), nullable=True),
        sa.Column("Validation_Status", sa.Enum("Pending", "Valid", "Failed"), nullable=False),
        sa.ForeignKeyConstraint(
            ["Bill_UUID"],
            ["publication_bills.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Config_ID"],
            ["publication_config.ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Created_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["FRBR_ID"],
            ["publication_frbr.ID"],
        ),
        sa.ForeignKeyConstraint(
            ["Modified_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_dso_state_exports",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("Export_Data", sa.JSON(), nullable=True),
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
        sa.Column("OW_ID_HASH", sa.String(length=64), nullable=False),
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
        sa.Column("Noemer", sa.Unicode(length=255), nullable=True),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("WID", sa.Unicode(), nullable=True),
        sa.Column("Geo_UUID", sa.Uuid(), nullable=True),
        sa.Column("Divisie_ref", sa.String(length=64), nullable=True),
        sa.Column("Bestuurlijke_grenzen_id", sa.Unicode(length=255), nullable=True),
        sa.Column("Domein", sa.Unicode(length=255), nullable=True),
        sa.Column("Geldig_Op", sa.Unicode(length=255), nullable=True),
        sa.Column("Ambtsgebied", sa.Unicode(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["Divisie_ref"],
            ["publication_ow_objects.OW_ID_HASH"],
        ),
        sa.ForeignKeyConstraint(
            ["Geo_UUID"],
            ["Werkingsgebieden.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Package_UUID"],
            ["publication_packages.UUID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
        sa.UniqueConstraint("OW_ID_HASH"),
    )
    op.create_table(
        "publication_package_reports",
        sa.Column("ID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Created_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("Result", sa.Unicode(), nullable=False),
        sa.Column("Report_Timestamp", sa.DateTime(), nullable=False),
        sa.Column("Messages", sa.Text(), nullable=True),
        sa.Column("Source_Document", sa.Text(), nullable=True),
        sa.Column("Report_Type", sa.Unicode(), nullable=False),
        sa.ForeignKeyConstraint(
            ["Created_By_UUID"],
            ["Gebruikers.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Package_UUID"],
            ["publication_packages.UUID"],
        ),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.create_table(
        "publication_ow_association",
        sa.Column("OW_ID_1_HASH", sa.String(length=64), nullable=False),
        sa.Column("OW_ID_2_HASH", sa.String(length=64), nullable=False),
        sa.Column("Type", sa.Unicode(), nullable=True),
        sa.ForeignKeyConstraint(
            ["OW_ID_1_HASH"],
            ["publication_ow_objects.OW_ID_HASH"],
        ),
        sa.ForeignKeyConstraint(
            ["OW_ID_2_HASH"],
            ["publication_ow_objects.OW_ID_HASH"],
        ),
        sa.PrimaryKeyConstraint("OW_ID_1_HASH", "OW_ID_2_HASH"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("publication_ow_association")
    op.drop_table("publication_package_reports")
    op.drop_table("publication_ow_objects")
    op.drop_table("publication_dso_state_exports")
    op.drop_table("publication_packages")
    op.drop_table("publication_bills")
    op.drop_table("publications")
    op.drop_table("publication_frbr")
    op.drop_table("publication_config")
    # ### end Alembic commands ###
