import pytest
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, Session, relationship, sessionmaker, mapped_column
from sqlalchemy.engine import Engine, create_engine

from app.core.db.mixins import HasIDType, TimeStamped, UserMetaData
from app.core.settings import settings
from app.dynamic.db.objects_table import ObjectBaseColumns
from app.dynamic.db.object_static_table import StaticBaseColumns
from app.extensions.modules.db.tables import (
    ModuleBaseColumns,
    ModuleObjectContextColumns,
    ModuleStatusHistoryColumns,
)
from app.extensions.modules.db.module_objects_tables import ModuleObjectsColumns

from app.extensions.modules.repository import (
    ModuleObjectRepository,
    ModuleObjectContextRepository,
    ModuleRepository,
    ObjectProvider,
    ModuleStatusRepository
)

from app.tests.fixtures import LocalTables, LocalTableFactory
from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
    ObjectFixtureFactory,
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
            ObjectStaticsTable=self.statics_table,
            ObjectsTable=self.objects_table,
            UsersTabel=self.users_table,
            ModuleTable=self._generate_module_table(),
            ModuleStatusHistoryTable=self._generate_status_history_table(),
            ModuleObjectContextTable=self._generate_object_context_table(),
            ModuleObjectsTable=self._generate_module_objects_table(),
        )

    def _generate_objects_table(self):
        class LocalObjectsTable(self.base, ObjectBaseColumns, TimeStamped, HasIDType, UserMetaData):
            __tablename__ = "objects"

            Title: Mapped[Optional[str]]
            Start_Validity: Mapped[datetime]
            End_Validity: Mapped[Optional[datetime]]
            ObjectStatics: Mapped["LocalObjectStaticsTable"] = relationship()

        return LocalObjectsTable

    def _generate_statics_table(self):
        # user_map = mapped_column(ForeignKey("Gebruikers.UUID"))
        class LocalObjectStaticsTable(self.base, StaticBaseColumns):
            __tablename__ = "object_statics"
            Owner_1_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))
            Owner_2_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))
            Client_1_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"))

        return LocalObjectStaticsTable

    def _generate_module_objects_table(self):
        class LocalModuleObjectsTable(
            self.base, ModuleObjectsColumns, TimeStamped, HasIDType, UserMetaData
        ):
            __tablename__ = "module_objects"

            Title: Mapped[Optional[str]]
            Start_Validity: Mapped[Optional[datetime]]
            End_Validity: Mapped[Optional[datetime]]

            ModuleObjectContext: Mapped[
                "LocalModuleObjectContextTable" # noqa
            ] = relationship()
            ObjectStatics: Mapped["LocalObjectStaticsTable"] = relationship(overlaps="ModuleObjectContext") # noqa

            __table_args__ = (
                ForeignKeyConstraint(
                    ["Module_ID", "Code"],
                    ["module_object_context.Module_ID", "module_object_context.Code"],
                ),
            )

        return LocalModuleObjectsTable

    def _generate_module_table(self):
        class LocalModuleTable(self.base, ModuleBaseColumns):
            __tablename__ = "modules"

            status_history: Mapped[
                List["LocalModuleStatusHistoryTable"] # noqa
            ] = relationship(
                back_populates="Module",
                order_by="asc(LocalModuleStatusHistoryTable.Created_Date)",
            )

            Created_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Created_By_UUID == LocalUsersTable.UUID"
            )
            Modified_By: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Modified_By_UUID == LocalUsersTable.UUID"
            )
            Module_Manager_1: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_1_UUID == LocalUsersTable.UUID"
            )
            Module_Manager_2: Mapped[List["LocalUsersTable"]] = relationship(
                primaryjoin="LocalModuleTable.Module_Manager_2_UUID == LocalUsersTable.UUID"
            )

        return LocalModuleTable

    def _generate_status_history_table(self):
        class LocalModuleStatusHistoryTable(self.base, ModuleStatusHistoryColumns):
            __tablename__ = "module_status_history"
            Module: Mapped["LocalModuleTable"] = relationship(back_populates="status_history")

        return LocalModuleStatusHistoryTable

    def _generate_object_context_table(self):
        class LocalModuleObjectContextTable(
            self.base, ModuleObjectContextColumns, TimeStamped, UserMetaData
        ):
            __tablename__ = "module_object_context"

        return LocalModuleObjectContextTable


@pytest.fixture(scope="class")
def local_tables():
    """
    Changed to setup DB once for class and
    run sequential tests with db data.
    """
    factory = ExtendedTableFactory()
    yield factory.local_tables


@pytest.fixture(scope="class")
def engine() -> Engine:
    engine = create_engine(
        settings.SQLALCHEMY_TEST_DATABASE_URI,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    yield engine


@pytest.fixture(scope="class")
def db(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()


@pytest.fixture(scope="class")
def setup_db_once(local_tables, engine):
    # setup db
    local_tables.Base.metadata.drop_all(engine)
    local_tables.Base.metadata.create_all(engine)
    yield local_tables
    # teardown
    local_tables.Base.metadata.drop_all(engine)


@pytest.fixture
def setup_db(local_tables, engine):
    # setup db
    local_tables.Base.metadata.drop_all(engine)
    local_tables.Base.metadata.create_all(engine)
    yield local_tables
    # teardown
    # local_tables.Base.metadata.drop_all(engine)


@pytest.fixture(scope="class")
def populate_users(db: Session):
    uf = UserFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture(scope="class")
def populate_statics(db: Session):
    uf = ObjectStaticsFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture(scope="class")
def populate_objects(db: Session, local_tables):
    now = datetime.now()
    five_days_ago = now - timedelta(days=5)
    five_days_later = now + timedelta(days=5)
    object_factory = ObjectFixtureFactory(db, local_tables)
    object_factory.create_all_objects()
    for obj in object_factory.objects:
        obj.Title = "monty"
        obj.Start_Validity = five_days_ago
        obj.End_Validity = five_days_later
    object_factory.populate_db()
    yield object_factory.objects


@pytest.fixture
def populate_modules(db: Session):
    uf = ModuleFixtureFactory(db)
    uf.create_all_objects()
    uf.create_all_module_status_history()
    uf.create_all_module_object_context()
    uf.create_all_module_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture
def module_repo(db: Session):
    return ModuleRepository(db=db)


@pytest.fixture
def module_context_repo(db: Session):
    return ModuleObjectContextRepository(db=db)


@pytest.fixture
def module_object_repo(db: Session):
    return ModuleObjectRepository(db=db)


@pytest.fixture
def object_provider(test_object_repository, module_object_repo):
    return ObjectProvider(
        object_repository=test_object_repository,
        module_object_repository=module_object_repo
    )
