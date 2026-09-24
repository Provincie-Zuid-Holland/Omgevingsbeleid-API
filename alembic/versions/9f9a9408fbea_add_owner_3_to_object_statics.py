"""add owner 3 to object statics

Revision ID: 9f9a9408fbea
Revises: 976ee7df9ee4
Create Date: 2026-09-16 06:55:14.408028

"""

import sqlalchemy as sa

from alembic import op
from app.core.db import table_metadata  ## noqa
from app.core.settings import Settings

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa

settings = Settings()


# revision identifiers, used by Alembic.
revision = "9f9a9408fbea"
down_revision = "976ee7df9ee4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("object_statics", sa.Column("Owner_3_UUID", sa.Uuid(), nullable=True))

    op.create_foreign_key("fk_object_statics_owner_3_uuid", "object_statics", "Gebruikers", ["Owner_3_UUID"], ["UUID"])


def downgrade() -> None:
    op.drop_constraint("fk_object_statics_owner_3_uuid", "object_statics", type_="foreignkey")

    op.drop_column("object_statics", "Owner_3_UUID")
