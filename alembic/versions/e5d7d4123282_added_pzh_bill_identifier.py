"""added pzh bill identifier

Revision ID: e5d7d4123282
Revises: 83ccd100b819
Create Date: 2024-02-07 19:01:17.962437

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa

from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "e5d7d4123282"
down_revision = "83ccd100b819"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "publication_bills",
        sa.Column("PZH_Bill_Identifier", sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("publication_bills", "PZH_Bill_Identifier")
