"""switch to date fields to prevent converting

Revision ID: 483e5cb75b78
Revises: e5d7d4123282
Create Date: 2024-02-07 20:27:15.402259

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa

from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "483e5cb75b78"
down_revision = "e5d7d4123282"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "publication_bills", "Effective_Date", existing_type=sa.DATETIME(), type_=sa.Date(), existing_nullable=True
    )
    op.alter_column(
        "publication_bills", "Announcement_Date", existing_type=sa.DATETIME(), type_=sa.Date(), existing_nullable=True
    )
    op.alter_column(
        "publication_frbr",
        "bill_expression_date",
        existing_type=sa.DATETIME(),
        type_=sa.Date(),
        existing_nullable=False,
    )
    op.alter_column(
        "publication_frbr",
        "act_expression_date",
        existing_type=mssql.DATETIMEOFFSET(),
        type_=sa.Date(),
        existing_nullable=False,
    )
    op.alter_column(
        "publication_packages",
        "Announcement_Date",
        existing_type=sa.DATETIME(),
        type_=sa.Date(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "publication_packages",
        "Announcement_Date",
        existing_type=sa.Date(),
        type_=sa.DATETIME(),
        existing_nullable=False,
    )
    op.alter_column(
        "publication_frbr",
        "act_expression_date",
        existing_type=sa.Date(),
        type_=mssql.DATETIMEOFFSET(),
        existing_nullable=False,
    )
    op.alter_column(
        "publication_frbr",
        "bill_expression_date",
        existing_type=sa.Date(),
        type_=sa.DATETIME(),
        existing_nullable=False,
    )
    op.alter_column(
        "publication_bills", "Announcement_Date", existing_type=sa.Date(), type_=sa.DATETIME(), existing_nullable=True
    )
    op.alter_column(
        "publication_bills", "Effective_Date", existing_type=sa.Date(), type_=sa.DATETIME(), existing_nullable=True
    )
