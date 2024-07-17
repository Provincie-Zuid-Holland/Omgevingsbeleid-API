from typing import List

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Mapped, Session, relationship

from app.dynamic.db import StaticBaseColumns
from app.extensions.acknowledged_relations.db.table_extensions.object_statics import extend_with_attributes
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationColumns
from app.extensions.acknowledged_relations.repository.acknowledged_relations_repository import (
    AcknowledgedRelationsRepository,
)
from app.tests.fixtures import LocalTableFactory, LocalTables


# Extend to add tables for acknowledged relation module
class ExtendedLocalTables(LocalTables):
    AcknowledgedRelationsTable: type


class ExtendedTableFactory(LocalTableFactory):
    def __init__(self):
        super().__init__()

    def _build_table(self) -> ExtendedLocalTables:
        return ExtendedLocalTables(
            Base=self.base,
            ObjectsTable=self._generate_objects_table(),
            ObjectStaticsTable=self._generate_statics_table(),
            UsersTabel=self._generate_users_table(),
            AcknowledgedRelationsTable=self._generate_ack_rel_table(),
        )

    def _generate_statics_table(self):
        class LocalObjectStaticsTable(self.base, StaticBaseColumns):
            __tablename__ = "object_statics"

            Objects: Mapped[List["LocalObjectsTable"]] = relationship(
                "LocalObjectsTable", back_populates="ObjectStatics", lazy="select"
            )

        extend_with_attributes(LocalObjectStaticsTable)
        return LocalObjectStaticsTable

    def _generate_ack_rel_table(self):
        class LocalAcknowledgedRelationsTable(self.base, AcknowledgedRelationColumns):
            __tablename__ = "acknowledged_relations"

            From_Object = relationship(
                "LocalObjectStaticsTable",
                primaryjoin="LocalAcknowledgedRelationsTable.From_Code == LocalObjectStaticsTable.Code",
                lazy="select",
            )
            To_Object = relationship(
                "LocalObjectStaticsTable",
                primaryjoin="LocalAcknowledgedRelationsTable.To_Code == LocalObjectStaticsTable.Code",
                lazy="select",
            )

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
    # local_tables.Base.metadata.drop_all(engine)


@pytest.fixture
def relation_repository(db: Session):
    return AcknowledgedRelationsRepository(db=db)
