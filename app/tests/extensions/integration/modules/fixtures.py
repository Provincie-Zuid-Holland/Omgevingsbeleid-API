import pytest
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Engine
from sqlalchemy.orm import Mapped, Session, relationship

from app.core.db.mixins import HasIDType, TimeStamped, UserMetaData
from app.extensions.modules.db.tables import (
    ModuleBaseColumns,
    ModuleObjectContextColumns,
    ModuleStatusHistoryColumns,
)
from app.extensions.modules.db.module_objects_tables import ModuleObjectsColumns

from app.tests.fixtures import LocalTables, LocalTableFactory
from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
    ModuleFixtureFactory,
)


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
            ModuleStatusHistoryTable=self._generate_status_history_table(),
            ModuleObjectContextTable=self._generate_object_context_table(),
            ModuleObjectsTable=self._generate_module_objects_table(),
        )

    def _generate_module_objects_table(self):
        class LocalModuleObjectsTable(
            self.base, ModuleObjectsColumns, TimeStamped, HasIDType
        ):
            __tablename__ = "module_objects"

            Start_Validity: Mapped[Optional[datetime]]
            End_Validity: Mapped[Optional[datetime]]

            ModuleObjectContext: Mapped[
                "LocalModuleObjectContextTable"
            ] = relationship()
            ObjectStatics: Mapped["LocalObjectStaticsTable"] = relationship()

        return LocalModuleObjectsTable

    def _generate_module_table(self):
        class LocalModuleTable(self.base, ModuleBaseColumns):
            __tablename__ = "modules"

            status_history: Mapped[
                List["LocalModuleStatusHistoryTable"]
            ] = relationship(
                back_populates="Module",
                order_by="asc(LocalModuleStatusHistoryTable.Created_Date)",
            )

            Created_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Created_By_UUID == UsersTable.UUID"
            )
            Modified_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Modified_By_UUID == UsersTable.UUID"
            )
            Module_Manager_1: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_1_UUID == UsersTable.UUID"
            )
            Module_Manager_2: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_2_UUID == UsersTable.UUID"
            )

        return LocalModuleTable

    def _generate_status_history_table(self):
        class LocalModuleStatusHistoryTable(self.base, ModuleStatusHistoryColumns):
            __tablename__ = "module_status_history"

        return LocalModuleStatusHistoryTable

    def _generate_object_context_table(self):
        class LocalModuleObjectContextTable(
            self.base, ModuleObjectContextColumns, TimeStamped, UserMetaData
        ):
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
    # local_tables.Base.metadata.drop_all(engine)


@pytest.fixture
def populate_users(db: Session):
    uf = UserFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture
def populate_statics(db: Session):
    uf = ObjectStaticsFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture
def populate_modules(db: Session):
    uf = ModuleFixtureFactory(db)
    uf.create_all_objects()
    uf.create_all_module_status_history()
    uf.create_all_module_object_context()
    uf.create_all_module_objects()
    uf.populate_db()
    yield uf.objects
