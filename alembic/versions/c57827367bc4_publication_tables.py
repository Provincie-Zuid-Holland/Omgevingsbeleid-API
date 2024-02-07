"""publication_tables

Revision ID: c57827367bc4
Revises: 00c1d7bd6337
Create Date: 2024-01-31 11:30:43.293795

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa


# revision identifiers, used by Alembic.
revision = "c57827367bc4"
down_revision = "00c1d7bd6337"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "publication_config",
        sa.Column("ID", sa.Integer(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Province_ID", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Authority_ID", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Submitter_ID", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Jurisdiction", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Subjects", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("DSO_STOP_VERSION", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("DSO_TPOD_VERSION", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("DSO_BHKV_VERSION", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.create_table(
        "publication_frbr",
        sa.Column("ID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column(
            "bill_work_country", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False
        ),
        sa.Column("bill_work_date", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("bill_work_misc", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column(
            "bill_expression_lang", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False
        ),
        sa.Column("bill_expression_date", sa.DateTime(), nullable=False),
        sa.Column(
            "bill_expression_version", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False
        ),
        sa.Column(
            "bill_expression_misc", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True
        ),
        sa.Column("act_work_country", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("act_work_date", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("act_work_misc", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column(
            "act_expression_lang", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False
        ),
        sa.Column("act_expression_date", sa.DateTime(255), nullable=False),
        sa.Column(
            "act_expression_version", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False
        ),
        sa.Column(
            "act_expression_misc", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True
        ),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.create_unique_constraint(
        "bill_unique_constraint", "publication_frbr", ["bill_work_misc", "bill_expression_version"]
    )
    op.create_unique_constraint(
        "act_unique_constraint", "publication_frbr", ["act_work_misc", "act_expression_version"]
    )
    op.create_table(
        "publications",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=True),
        sa.Column("Modified_Date", sa.DateTime(), nullable=True),
        sa.Column("Module_ID", sa.Integer(), nullable=False),
        sa.Column("Template_ID", sa.Integer(), nullable=True),
        sa.Column("Work_ID", sa.Integer(), nullable=False),
        sa.Column("Official_Title", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Regulation_Title", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column(
            "Document_Type", sa.Enum("Omgevingsvisie", "Omgevingsprogramma", "Omgevingsverordening"), nullable=True
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
        sa.Column("Publication_UUID", sa.Uuid(), nullable=False),
        sa.Column("Module_Status_ID", sa.Integer(), nullable=False),
        sa.Column("Version_ID", sa.Integer(), nullable=False),
        sa.Column("Is_Official", sa.Boolean(), nullable=False),
        sa.Column("Effective_Date", sa.DateTime(), nullable=True),
        sa.Column("Announcement_Date", sa.DateTime(), nullable=True),
        sa.Column("Procedure_Type", sa.Enum("Ontwerp", "Definitief"), nullable=False),
        sa.Column("Bill_Data", sa.JSON(), nullable=True),
        sa.Column("Procedure_Data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["Publication_UUID"],
            ["publications.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Module_Status_ID"],
            ["module_status_history.ID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_table(
        "publication_packages",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Bill_UUID", sa.Uuid(), nullable=False),
        sa.Column("Config_ID", sa.Integer(), nullable=False),
        sa.Column("FRBR_ID", sa.Integer(), nullable=False),
        sa.Column("Publication_Filename", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Announcement_Date", sa.DateTime(), nullable=False),
        sa.Column("Package_Event_Type", sa.Enum("Validatie", "Publicatie", "Afbreken"), nullable=False),
        sa.ForeignKeyConstraint(
            ["Bill_UUID"],
            ["publication_bills.UUID"],
        ),
        sa.ForeignKeyConstraint(
            ["Config_ID"],
            ["publication_config.ID"],
        ),
        sa.ForeignKeyConstraint(
            ["FRBR_ID"],
            ["publication_frbr.ID"],
        ),
        sa.PrimaryKeyConstraint("UUID"),
        sa.UniqueConstraint("FRBR_ID"),
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
        sa.Column("OW_ID", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
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
        sa.Column("Noemer", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("WID", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Geo_UUID", sa.Uuid(), nullable=True),
        sa.Column("Divisie_ref", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Bestuurlijke_grenzen_id", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Domein", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Geldig_Op", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.Column("Ambtsgebied", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
        sa.ForeignKeyConstraint(
            ["Divisie_ref"],
            ["publication_ow_objects.OW_ID"],
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
        sa.UniqueConstraint("OW_ID"),
    )
    op.create_table(
        "publication_ow_association",
        sa.Column("OW_ID_1", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("OW_ID_2", sa.VARCHAR(length=255, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Type", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
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
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("publication_ow_association")
    op.drop_table("publication_ow_objects")
    op.drop_table("publication_dso_state_exports")
    op.drop_table("publication_packages")
    op.drop_table("publication_bills")
    op.drop_table("publications")
    op.drop_table("publication_frbr")
    op.drop_table("publication_config")
    # ### end Alembic commands ###