import pytest
from typing import List

from sqlalchemy import Engine
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.tests.fixtures import LocalTables, LocalTableFactory
from app.extensions.modules.db.tables import (
    ModuleBaseColumns,
    ModuleObjectContextColumns,
    ModuleStatusHistoryColumns,
)
from app.extensions.modules.db.module_objects_tables import ModuleObjectsColumns


## Add Child classes to probide tables for this extension
class ExtendedLocalTables(LocalTables):
    ModuleTable: type
    ModuleObjectsTable: type
    ModuleStatusHistoryTable: type
    ModuleObjectContextTable: type


class ExtendedTableFactory(LocalTableFactory):
    def __init__(self):
        super().__init__()

    def _build_table(self) -> ExtendedLocalTables:
        return ExtendedLocalTables(
            Base=self.base,
            ObjectsTable=self.objects_table,
            ObjectStaticsTable=self.statics_table,
            UsersTabel=self.users_table,
            ModuleTable=self._generate_module_table(),
            ModuleStatusHistoryTable=self._generate_objects_table(),
            ModuleObjectContextTable=self._generate_object_context_table(),
            ModuleObjectsTable=self._generate_module_objects_table()
        )

    def _generate_module_objects_table(self):
        class LocalModuleObjectsTable(self.base, ModuleObjectsColumns):
            __tablename__ = "module_objects"

        return LocalModuleObjectsTable

    def _generate_module_table(self):
        class LocalModuleTable(self.base, ModuleBaseColumns):
            __tablename__ = "modules"

            status_history: Mapped[List["LocalModuleStatusHistoryTable"]] = relationship(
                back_populates="Module", order_by="asc(LocalModuleStatusHistoryTable.Created_Date)"
            )

            Created_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Created_By_UUID == UsersTable.UUID"
            )
            Modified_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Modified_By_UUID == UsersTable.UUID"
            )
            Module_Manager_1: Mapped[List["UsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_1_UUID == UsersTable.UUID"
            )
            Module_Manager_2: Mapped[List["UsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_2_UUID == UsersTable.UUID"
            )

        return LocalModuleTable

    def _generate_status_history_table(self):
        class LocalModuleStatusHistoryTable(self.base, ModuleStatusHistoryColumns):
            __tablename__ = "module_status_history"

        return LocalModuleStatusHistoryTable

    def _generate_object_context_table(self):
        class LocalModuleObjectContextTable(self.base, ModuleObjectContextColumns):
            __tablename__ = "module_object_context"

        return LocalModuleObjectContextTable


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
