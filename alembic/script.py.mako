"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa

# We need these to load all sqlalchemy tables
from app.main import app  ## noqa 
from app.core.db import table_metadata  ## noqa 
from app.core.settings import Settings  ## noqa
from app.core.db.geometry import Geometry  ## noqa

settings = Settings()

${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
