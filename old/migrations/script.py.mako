"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
import Api.Utils

app.util.sqlalchemy
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}


def dialect_supports_sequences():
    return op._proxy.migration_context.dialect.supports_sequences


def dialect_supports_geometry_index():
    return op._proxy.migration_context.dialect.name == 'mssql'


def create_seq(name):
    if dialect_supports_sequences():
       op.execute(sa.schema.CreateSequence(sa.schema.Sequence(name)))


def drop_seq(name):
    if dialect_supports_sequences():
       op.execute(sa.schema.DropSequence(sa.schema.Sequence(name)))
