"""add hoofdlijnen

Revision ID: 80143fa75c0b
Revises: c704f8f17f09
Create Date: 2026-06-15 12:57:20.097495

"""

import sqlalchemy as sa

from alembic import op
from app.core.db import table_metadata  ## noqa
from app.core.settings import Settings  ## noqa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa

settings = Settings()


# revision identifiers, used by Alembic.
revision = "80143fa75c0b"
down_revision = "c704f8f17f09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hoofdlijnen",
        sa.Column("UUID", sa.Uuid(), nullable=False),
        sa.Column("Name", sa.Unicode(length=255), nullable=False),
        sa.Column("Type", sa.Unicode(length=255), nullable=False),
        sa.Column("Created_Date", sa.DateTime(), nullable=False),
        sa.Column("Modified_Date", sa.DateTime(), nullable=False),
        sa.Column("Deleted_Date", sa.DateTime(), nullable=True),
        sa.Column("Created_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False),
        sa.Column("Deleted_By_UUID", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["Created_By_UUID"], ["Gebruikers.UUID"], ),
        sa.ForeignKeyConstraint(["Modified_By_UUID"], ["Gebruikers.UUID"], ),
        sa.ForeignKeyConstraint(["Deleted_By_UUID"], ["Gebruikers.UUID"], ),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_index(op.f("ix_hoofdlijnen_Name_Type"), "hoofdlijnen", ["Name", "Type"], unique=True)
    op.add_column("module_objects", sa.Column("Hoofdlijnen", sa.JSON(), nullable=True))
    op.add_column("objects", sa.Column("Hoofdlijnen", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("objects", "Hoofdlijnen")
    op.drop_column("module_objects", "Hoofdlijnen")
    op.drop_table("hoofdlijnen")
