from dataclasses import dataclass
from typing import Generator
import uuid

from fastapi import FastAPI
import pytest
from dependency_injector import providers
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient


# Importing app.main triggers the full YAML -> tables -> models -> routes build.
from app.api.api_container import ApiContainer
import app.main as _app_module  # noqa: F401
from app.api.domains.users.services.security import Security
from app.core.db.base import Base
from app.core.db.session import _enable_sqlite_load_extension
from tests.fixtures.internal.fixtures_service import FixturesService
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import FixtureData, Ref


@dataclass
class Context:
    session: Session
    fixtures: FixtureData

    @property
    def s(self) -> Session:
        return self.session

    @property
    def f(self) -> FixtureData:
        return self.fixtures


@pytest.fixture(scope="session")
def engine():
    """
    Single in-memory SQLite engine for the whole test session.

    StaticPool ensures all connections share one underlying connection, so
    in-memory tables created by create_all() are visible to all subsequent
    queries. check_same_thread=False lets pytest fixtures and the app code
    share the connection across threads (TestClient uses a background thread).
    """
    _engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(_engine, "connect")
    def _sqlite_connect(dbapi_connection, connection_record) -> None:
        # Hand BEGIN control to SQLAlchemy. sqlite3's legacy transaction mode
        # does not emit BEGIN for SELECT/DDL and does not let a SAVEPOINT
        # participate in the enclosing transaction, so a released savepoint is
        # not rolled back by transaction.rollback().
        # Disabling the driver's BEGIN and emitting it ourselves (see the
        # "begin" listener) is the documented fix:
        # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#transactions-with-sqlite-and-the-sqlite3-driver
        dbapi_connection.isolation_level = None

        # Load mod_spatialite for the geo tests that need it.
        _enable_sqlite_load_extension(dbapi_connection, connection_record)

        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    @event.listens_for(_engine, "begin")
    def _sqlite_emit_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN")

    # Build all tables now that app.main has been imported and populated Base.metadata.
    Base.metadata.create_all(_engine)

    yield _engine

    _engine.dispose()


@pytest.fixture(scope="session")
def seed_data(engine) -> FixtureData:
    connection = engine.connect()
    factory = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)
    data: FixtureData = FixtureData()
    with factory() as session:
        data = FixturesService().load(session)
        session.commit()
    connection.close()
    return data


@pytest.fixture()
def _test_env(engine, seed_data) -> Generator[Context, None, None]:
    connection = engine.connect()
    transaction = connection.begin()

    TestSession = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",  # app's .begin()-commit -> savepoint release
    )

    app: FastAPI = _app_module.app
    container: ApiContainer = app.container

    previous_sessionmaker = app.state.db_sessionmaker
    app.state.db_sessionmaker = TestSession
    container.db_session_factory.override(providers.Object(TestSession))

    session = TestSession()
    try:
        yield Context(session=session, fixtures=seed_data)
    finally:
        session.close()
        container.db_session_factory.reset_override()
        app.state.db_sessionmaker = previous_sessionmaker
        transaction.rollback()
        connection.close()


@pytest.fixture()
def ctx(_test_env) -> Context:
    """One dependency carrying both the session and the fixture lookups."""
    return _test_env


@pytest.fixture()
def session(_test_env: Context) -> Session:
    return _test_env.session


@pytest.fixture()
def fixtures(_test_env: Context) -> FixtureData:
    return _test_env.fixtures


@pytest.fixture()
def security() -> Security:
    return _app_module.app.container.security()


@pytest.fixture()
def client(_test_env) -> Generator[TestClient, None, None]:
    # Depends on _test_env so the overrides are active before any request runs.
    with TestClient(_app_module.app) as test_client:
        yield test_client


def _client_logged_in_as(security: Security, user_uuid: uuid.UUID) -> Generator[TestClient, None, None]:
    """A TestClient pre-authenticated as the given user.

    Mints a JWT with the container's Security service (same SECRET_KEY the app
    decodes with) and presets the Authorization header, so every request the
    client makes is authenticated as that user.
    """
    token = security.create_access_token(user_uuid)
    with TestClient(_app_module.app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client


@pytest.fixture()
def admin(_test_env: Context, security: Security) -> Generator[TestClient, None, None]:
    """A TestClient logged in as the seeded 'admin' user."""
    admin_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "admin"))
    yield from _client_logged_in_as(security, admin_uuid)


@pytest.fixture()
def ambtenaar(_test_env: Context, security: Security) -> Generator[TestClient, None, None]:
    ambtenaar_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "ambtenaar"))
    yield from _client_logged_in_as(security, ambtenaar_uuid)
