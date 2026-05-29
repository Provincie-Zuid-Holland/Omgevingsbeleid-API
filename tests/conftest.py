import pytest
from dependency_injector import providers
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Importing app.main triggers the full YAML -> tables -> models -> routes build.
import app.main as _app_module
from app.api.api_container import ApiContainer
from app.core.db.base import Base
from app.core.db.session import _enable_sqlite_load_extension


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
    event.listen(_engine, "connect", _enable_sqlite_load_extension)

    # Build all tables now that app.main has been imported and populated Base.metadata.
    Base.metadata.create_all(_engine)

    yield _engine

    _engine.dispose()


@pytest.fixture()
def db_session(engine):
    """
    Per-test transactional session using SAVEPOINTs.

    Opens one connection-level transaction at the start of each test and rolls
    it back at the end, so tests don't share state. join_transaction_mode=
    "create_savepoint" means that when application code calls sessionmaker.begin()
    (as depends_db_session does), SQLAlchemy creates a SAVEPOINT rather than
    trying to start a new top-level transaction.
    """
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
