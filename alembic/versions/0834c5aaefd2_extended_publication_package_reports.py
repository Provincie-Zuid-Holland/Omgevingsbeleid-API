"""extended publication package reports

Revision ID: 0834c5aaefd2
Revises: c57827367bc4
Create Date: 2024-02-04 20:58:02.214193

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa

from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "0834c5aaefd2"
down_revision = "c57827367bc4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publication_package_reports",
        sa.Column("ID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Package_UUID", sa.Uuid(), nullable=False),
        sa.Column("Result", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.Column("Report_Timestamp", sa.DateTime(), nullable=False),
        sa.Column("Messages", sa.Text(), nullable=True),
        sa.Column("Source_Document", sa.Text(), nullable=True),
        sa.Column("Report_Type", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=False),
        sa.ForeignKeyConstraint(
            ["Package_UUID"],
            ["publication_packages.UUID"],
        ),
        sa.PrimaryKeyConstraint("ID"),
    )
    op.add_column(
        "publication_packages",
        sa.Column("ZIP_File_Name", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
    )
    op.add_column("publication_packages", sa.Column("ZIP_File_Binary", sa.LargeBinary(), nullable=True))
    op.add_column(
        "publication_packages",
        sa.Column("ZIP_File_Checksum", sa.VARCHAR(length=64, collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
    )

    op.add_column(
        "publication_packages",
        sa.Column("Validation_Status", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("publication_packages", "ZIP_File_Checksum")
    op.drop_column("publication_packages", "ZIP_File_Binary")
    op.drop_column("publication_packages", "ZIP_File_Name")
    op.drop_column("publication_packages", "Validation_Status")
    op.drop_table("publication_package_reports")
