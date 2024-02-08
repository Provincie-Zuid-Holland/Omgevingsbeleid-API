"""publications created by tracking

Revision ID: 70e7562b7f51
Revises: 483e5cb75b78
Create Date: 2024-02-08 11:17:15.644171

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa
from app.core.db import table_metadata  ## noqa
from app.core.settings import settings  ## noqa


# revision identifiers, used by Alembic.
revision = "70e7562b7f51"
down_revision = "483e5cb75b78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("publication_bills", sa.Column("Created_By_UUID", sa.Uuid(), nullable=False))
    op.add_column("publication_bills", sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False))
    op.create_foreign_key(None, "publication_bills", "Gebruikers", ["Modified_By_UUID"], ["UUID"])
    op.create_foreign_key(None, "publication_bills", "Gebruikers", ["Created_By_UUID"], ["UUID"])
    op.add_column("publication_package_reports", sa.Column("Created_By_UUID", sa.Uuid(), nullable=False))
    op.create_foreign_key(None, "publication_package_reports", "Gebruikers", ["Created_By_UUID"], ["UUID"])
    op.add_column("publication_packages", sa.Column("Created_By_UUID", sa.Uuid(), nullable=False))
    op.add_column("publication_packages", sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False))
    op.create_foreign_key(None, "publication_packages", "Gebruikers", ["Created_By_UUID"], ["UUID"])
    op.create_foreign_key(None, "publication_packages", "Gebruikers", ["Modified_By_UUID"], ["UUID"])
    op.add_column("publications", sa.Column("Created_By_UUID", sa.Uuid(), nullable=False))
    op.add_column("publications", sa.Column("Modified_By_UUID", sa.Uuid(), nullable=False))
    op.create_foreign_key(None, "publications", "Gebruikers", ["Created_By_UUID"], ["UUID"])
    op.create_foreign_key(None, "publications", "Gebruikers", ["Modified_By_UUID"], ["UUID"])


def downgrade() -> None:
    op.drop_constraint(None, "publications", type_="foreignkey")
    op.drop_constraint(None, "publications", type_="foreignkey")
    op.drop_column("publications", "Modified_By_UUID")
    op.drop_column("publications", "Created_By_UUID")
    op.drop_constraint(None, "publication_packages", type_="foreignkey")
    op.drop_constraint(None, "publication_packages", type_="foreignkey")
    op.drop_column("publication_packages", "Modified_By_UUID")
    op.drop_column("publication_packages", "Created_By_UUID")
    op.drop_constraint(None, "publication_package_reports", type_="foreignkey")
    op.drop_column("publication_package_reports", "Created_By_UUID")
    op.drop_constraint(None, "publication_bills", type_="foreignkey")
    op.drop_constraint(None, "publication_bills", type_="foreignkey")
    op.drop_column("publication_bills", "Modified_By_UUID")
    op.drop_column("publication_bills", "Created_By_UUID")
