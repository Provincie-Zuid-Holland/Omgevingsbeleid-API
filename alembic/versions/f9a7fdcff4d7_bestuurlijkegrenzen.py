"""bestuurlijkegrenzen

Revision ID: f9a7fdcff4d7
Revises: da2cc1de90bd
Create Date: 2024-02-14 13:33:11.018431

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa


# revision identifiers, used by Alembic.
revision = "f9a7fdcff4d7"
down_revision = "da2cc1de90bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("publication_config", sa.Column("Administrative_Borders_ID", sa.Unicode(length=255), nullable=False))
    op.add_column(
        "publication_config", sa.Column("Administrative_Borders_Domain", sa.Unicode(length=255), nullable=False)
    )
    op.add_column("publication_config", sa.Column("Administrative_Borders_Date", sa.Date(), nullable=False))


def downgrade() -> None:
    op.drop_column("publication_config", "Administrative_Borders_Date")
    op.drop_column("publication_config", "Administrative_Borders_Domain")
    op.drop_column("publication_config", "Administrative_Borders_ID")
