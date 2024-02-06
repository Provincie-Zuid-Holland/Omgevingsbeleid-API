"""extended publication config fields

Revision ID: 83ccd100b819
Revises: 0834c5aaefd2
Create Date: 2024-02-06 16:04:56.557039

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa

from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "83ccd100b819"
down_revision = "0834c5aaefd2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Governing_Body_Type column with default value
    op.add_column(
        "publication_config",
        sa.Column(
            "Governing_Body_Type",
            sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"),
            nullable=False,
            server_default="Provinciale_staten",
        ),
    )
    # Update the column to remove the server_default if not needed permanently
    op.alter_column("publication_config", "Governing_Body_Type", server_default=None)

    # Add Act_Componentname column with default value
    op.add_column(
        "publication_config",
        sa.Column(
            "Act_Componentname",
            sa.VARCHAR(collation="SQL_Latin1_General_CP1_CI_AS"),
            nullable=False,
            server_default="nieuweregeling",
        ),
    )
    # Update the column to remove the server_default if not needed permanently
    op.alter_column("publication_config", "Act_Componentname", server_default=None)


def downgrade() -> None:
    op.drop_column("publication_config", "Act_Componentname")
    op.drop_column("publication_config", "Governing_Body_Type")
