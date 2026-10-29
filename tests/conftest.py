import uuid
from collections.abc import AsyncGenerator, Generator

import httpx2
import pytest
from dependency_injector import providers
from fastapi import FastAPI
from freezegun import freeze_time
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.main as _app_module

# Importing app.main triggers the full YAML -> tables -> models -> routes build.
from app.api.api_container import ApiContainer
from app.api.domains.users.services.security import Security
from app.core.db.base import Base
from app.core.db.session import _enable_aiosqlite_extensions
from app.core.services.models_provider import ModelsProvider
from tests.fixtures.internal.fixtures_service import FixturesService
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Context, FixtureData, Ref

# Fixtures live in 2025; the suite runs as if it were this moment.
FROZEN_NOW = "2026-01-01"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _frozen_time() -> Generator[None]:
    with freeze_time(FROZEN_NOW, real_asyncio=True):
        yield


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    """
    Single in-memory SQLite engine for the whole test session.

    StaticPool ensures all connections share one underlying connection, so
    in-memory tables created by create_all() are visible to all subsequent
    queries.
    """
    _engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(_engine.sync_engine, "connect")
    def _sqlite_connect(dbapi_connection, connection_record) -> None:
        dbapi_connection.isolation_level = None

        # Loads mod_spatialite for the geo tests and turns on foreign keys
        _enable_aiosqlite_extensions(dbapi_connection, connection_record)

    @event.listens_for(_engine.sync_engine, "begin")
    def _sqlite_emit_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN")

    # Build all tables now that app.main has been imported and populated Base.metadata.
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield _engine

    await _engine.dispose()


@pytest.fixture(scope="session")
async def seed_data(engine: AsyncEngine) -> FixtureData:
    async with engine.connect() as connection:
        async with AsyncSession(bind=connection, autoflush=False, expire_on_commit=False) as session:
            # Defer FK checks until commit so fixtures can load in any order.
            await session.execute(text("PRAGMA defer_foreign_keys = ON"))
            data: FixtureData = await FixturesService().load(session)
            await session.commit()
        return data


@pytest.fixture(autouse=True)
async def _test_env(engine: AsyncEngine, seed_data: FixtureData) -> AsyncGenerator[Context]:
    connection = await engine.connect()
    transaction = await connection.begin()

    TestSession = async_sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",  # app's .begin()-commit -> savepoint release
    )

    app: FastAPI = _app_module.app
    container: ApiContainer = app.container

    previous_sessionmaker = app.state.db_sessionmaker
    app.state.db_sessionmaker = TestSession
    container.db_session_factory.override(providers.Object(TestSession))

    session: AsyncSession = TestSession()
    try:
        yield Context(
            session=session,
            fixtures=seed_data,
            models_provider=container.models_provider(),
        )
    finally:
        await session.close()
        container.db_session_factory.reset_override()
        app.state.db_sessionmaker = previous_sessionmaker
        await transaction.rollback()
        await connection.close()


@pytest.fixture()
def ctx(_test_env) -> Context:
    """One dependency carrying both the session and the fixture lookups."""
    return _test_env


@pytest.fixture()
def session(_test_env: Context) -> AsyncSession:
    return _test_env.session


@pytest.fixture()
def fixtures(_test_env: Context) -> FixtureData:
    return _test_env.fixtures


@pytest.fixture()
def security() -> Security:
    return _app_module.app.container.security()


@pytest.fixture()
def models_provider(_test_env: Context) -> ModelsProvider:
    return _test_env.models_provider


def _new_client() -> httpx2.AsyncClient:
    return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=_app_module.app), base_url="http://test")


@pytest.fixture()
def client(_test_env) -> httpx2.AsyncClient:
    # Depends on _test_env so the overrides are active before any request runs.
    return _new_client()


def _client_logged_in_as(security: Security, user_uuid: uuid.UUID) -> httpx2.AsyncClient:
    """An AsyncClient pre-authenticated as the given user.

    Mints a JWT with the container's Security service (same SECRET_KEY the app
    decodes with) and presets the Authorization header, so every request the
    client makes is authenticated as that user.
    """
    token = security.create_access_token(user_uuid)
    test_client = _new_client()
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client


@pytest.fixture()
def admin(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    """A client logged in as the seeded 'admin' user."""
    admin_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "admin"))
    return _client_logged_in_as(security, admin_uuid)


@pytest.fixture()
def ambtenaar(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    ambtenaar_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "ambtenaar"))
    return _client_logged_in_as(security, ambtenaar_uuid)


@pytest.fixture()
def manager_of_module_4(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    ambtenaar_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "manager_of_module_4"))
    return _client_logged_in_as(security, ambtenaar_uuid)


@pytest.fixture()
def owner_1(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    owner_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "owner_1"))
    return _client_logged_in_as(security, owner_uuid)


@pytest.fixture()
def owner_3(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    owner_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "owner_3"))
    return _client_logged_in_as(security, owner_uuid)


@pytest.fixture()
def viewer(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    viewer_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "viewer"))
    return _client_logged_in_as(security, viewer_uuid)


@pytest.fixture()
def beheerder(_test_env: Context, security: Security) -> httpx2.AsyncClient:
    beheerder_uuid: uuid.UUID = _test_env.fixtures.primary_key_uuid(Ref(UserSpec, "beheerder"))
    return _client_logged_in_as(security, beheerder_uuid)
