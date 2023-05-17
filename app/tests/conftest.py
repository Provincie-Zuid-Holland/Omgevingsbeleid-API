from typing import Generator, List
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from app.core.settings import settings
from app.dynamic.converter import Converter, ObjectConverterData
from app.dynamic.dynamic_app import DynamicAppBuilder
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.repository.object_static_repository import ObjectStaticRepository
from app.extensions.auth.auth_extension import AuthExtension
from app.extensions.database_migration.database_migration_extension import (
    DatabaseMigrationExtension,
)
from app.extensions.extended_users.extended_user_extension import ExtendedUserExtension
from app.extensions.users.users_extension import UsersExtension
from app.tests.helpers import patch_multiple
from app.tests.fixtures import TestDynamicApp, LocalTableFactory, MockPermissionService
from app.tests.fixture_factories import MasterFixtureFactory


class TestSettings:
    BASE_TEST_CONFIG_FILE: str = "./app/tests/config/main_base.yml"
    TEST_OBJECT_CONFIG_PATH: str = "./app/tests/config/objects/"
    BASE_EXTENSIONS: List = [
        UsersExtension(),
        AuthExtension(),
        ExtendedUserExtension(),
        DatabaseMigrationExtension(),
    ]


@pytest.fixture(scope="function")
def engine() -> Engine:
    if settings.SQLALCHEMY_TEST_DATABASE_URI is None:
        raise Exception("Missing Test DB connection URI")

    engine = create_engine(
        settings.SQLALCHEMY_TEST_DATABASE_URI,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    yield engine


@pytest.fixture(scope="function")
def db(engine) -> Generator:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()
    print("Teardown Session")


@pytest.fixture
def local_tables(engine):
    factory = LocalTableFactory()
    local_tables = factory.local_tables

    # Setup db
    local_tables.Base.metadata.drop_all(engine)
    local_tables.Base.metadata.create_all(engine)

    yield local_tables

    # Teardown
    # local_tables.Base.metadata.drop_all(engine)


@pytest.fixture
def master_factory(db):
    # TODO
    yield MasterFixtureFactory(db)


@pytest.fixture
def populate_db(master_factory):
    raise Exception("Not implemented")
    # factory.create_all_objects()
    # factory.populate_db()
    # yield factory


@pytest.fixture(scope="function")
def mock_permission_service():
    service = MockPermissionService(give_permission=True)
    yield service


@pytest.fixture
def mock_converter():
    basic_converter = ObjectConverterData(
        column_deserializers=dict(),
        field_serializers=dict(),
    )

    converter = Converter()
    converter._per_object_id["ambitie"] = basic_converter
    return converter


@pytest.fixture
def mock_dispatcher():
    event_dispatcher_mock = MagicMock(spec=EventDispatcher)
    return event_dispatcher_mock


@pytest.fixture
def test_object_repository(db: Session):
    return ObjectRepository(db=db)


@pytest.fixture
def test_object_static_repository(db: Session):
    return ObjectStaticRepository(db=db)


@pytest.fixture(scope="function")
def base_dynamic_app(local_tables) -> TestDynamicApp:  # noqa
    with patch_multiple(
        patch("app.core.db.base.Base", local_tables.Base),
        patch("app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable),
        patch(
            "app.dynamic.db.object_static_table.ObjectStaticsTable",
            local_tables.ObjectStaticsTable,
        ),
    ):
        builder = DynamicAppBuilder(TestSettings.BASE_TEST_CONFIG_FILE)
        for ext in TestSettings.BASE_EXTENSIONS:
            builder.register_extension(ext)

        builder.register_objects(TestSettings.TEST_OBJECT_CONFIG_PATH)
        dynamic_app = builder.build()
        return TestDynamicApp(dynamic_app=dynamic_app, local_tables=local_tables)
