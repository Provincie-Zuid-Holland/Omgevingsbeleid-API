"""act_package_module_status

Revision ID: c704f8f17f09
Revises: 7abe9ef050cf
Create Date: 2026-07-16 11:14:38.119865

"""

from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import Settings  ## noqa

settings = Settings()


# revision identifiers, used by Alembic.
revision = "c704f8f17f09"
down_revision = "7abe9ef050cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("publication_act_packages", sa.Column("Module_ID", sa.Integer(), nullable=True))
    op.add_column("publication_act_packages", sa.Column("Module_Status_ID", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_publication_act_packages_module_id", "publication_act_packages", "modules", ["Module_ID"], ["Module_ID"]
    )
    op.create_foreign_key(
        "fk_publication_act_packages_module_status_id",
        "publication_act_packages",
        "module_status_history",
        ["Module_Status_ID"],
        ["ID"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_publication_act_packages_module_status_id", "publication_act_packages", type_="foreignkey")
    op.drop_constraint("fk_publication_act_packages_module_id", "publication_act_packages", type_="foreignkey")
    op.drop_column("publication_act_packages", "Module_Status_ID")
    op.drop_column("publication_act_packages", "Module_ID")
