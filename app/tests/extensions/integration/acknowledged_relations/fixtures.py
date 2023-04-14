import pytest

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.tests.fixtures import LocalTables, LocalTableFactory
from app.extensions.acknowledged_relations.db.tables import (
    AcknowledgedRelationColumns,
)


# Extend to add tables for acknowledged relation module
class ExtendedLocalTables(LocalTables):
    AcknowledgedRelationsTable: type


class ExtendedTableFactory(LocalTableFactory):
    def __init__(self):
        super().__init__()

    def _build_table(self) -> ExtendedLocalTables:
        return ExtendedLocalTables(
            Base=self.base,
            ObjectsTable=self.objects_table,
            ObjectStaticsTable=self.statics_table,
            UsersTabel=self.users_table,
            AcknowledgedRelationsTable=self._generate_ack_rel_table(),
        )

    def _generate_ack_rel_table(self):
        class LocalAcknowledgedRelationsTable(self.base, AcknowledgedRelationColumns):
            __tablename__ = "acknowledged_relations"

        return LocalAcknowledgedRelationsTable


@pytest.fixture
def local_tables(db: Session, engine: Engine):
    factory = ExtendedTableFactory()
    local_tables = factory.local_tables

    # setup db
    local_tables.Base.metadata.drop_all(engine)
    local_tables.Base.metadata.create_all(engine)

    yield local_tables
    # teardown db
    local_tables.Base.metadata.drop_all(engine)
