from unittest.mock import patch
import uuid
from typing import Generator, List, Optional

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
    sessionmaker,
)

from app.core.settings import settings
from app.dynamic.dynamic_app import DynamicAppBuilder
from app.dynamic.db import ObjectStaticsTable
from app.extensions.auth.auth_extension import AuthExtension
from app.extensions.database_migration.database_migration_extension import (
    DatabaseMigrationExtension,
)
from app.extensions.extended_users.extended_user_extension import ExtendedUserExtension
from app.extensions.users.users_extension import UsersExtension
from app.tests.helpers import LocalTables, TestDynamicApp, patch_multiple


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
    # db.rollback()
    # db.close()


@pytest.fixture
def local_tables() -> LocalTables:
    TestBase = declarative_base()

    # Find a way to auto-generate?
    class LocalObjectsTable(TestBase):
        __tablename__ = "objects"

        UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
        Code: Mapped[str] = mapped_column(String(35), ForeignKey("object_statics.Code"))

        object_statics: Mapped["ObjectStaticsTable"] = relationship()

    class LocalObjectStaticsTable(TestBase):
        __tablename__ = "object_statics"

        Object_Type: Mapped[str] = mapped_column(String(25))
        Object_ID: Mapped[int]
        Code: Mapped[str] = mapped_column(String(35), primary_key=True)

        def __repr__(self) -> str:
            return f"ObjectStatics(Code={self.Code!r}"

    class LocalUsersTable(TestBase):
        __tablename__ = "Gebruikers"

        UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
        Gebruikersnaam: Mapped[Optional[str]]
        Email: Mapped[str] = mapped_column(unique=True)
        Rol: Mapped[Optional[str]]
        Status: Mapped[Optional[str]]
        # @todo; do not fetch when not needed
        Wachtwoord: Mapped[Optional[str]]  # = mapped_column(deferred=True)

        @property
        def IsActief(self) -> bool:
            return self.Status == "Actief"

        def __repr__(self) -> str:
            return f"Gebruikers(UUID={self.UUID!r}, Gebruikersnaam={self.Gebruikersnaam!r})"

    return LocalTables(
        Base=TestBase,
        ObjectsTable=LocalObjectsTable,
        ObjectStaticsTable=LocalObjectStaticsTable,
        UsersTabel=LocalUsersTable,
    )


@pytest.fixture(scope="function")
def base_dynamic_app(local_tables) -> TestDynamicApp:
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


# @pytest.fixture(scope="module")
# def client() -> Generator:
#     # Dynamic app?
#     app.dependency_overrides[depends_db] = get_test_db
#     # Dep override get_db
#     with TestClient(app) as c:
#         yield c


# @pytest.fixture(scope="class")
# def fixture_data(db: Session):
#     engine = db.get_bind()
#     table_metadata.drop_all(bind=engine)
#     table_metadata.create_all(bind=engine)

#     loader = DatabaseFixtures(db)
#     loader.create_all()
#     yield loader


# @pytest.fixture(scope="module")
# def superuser_token_headers(client: TestClient) -> Dict[str, str]:
#     return get_superuser_token_headers(client)


# @pytest.fixture(scope="module")
# def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
#     return authentication_token_from_email(
#         client=client, email=settings.EMAIL_TEST_USER, db=db
#     )
