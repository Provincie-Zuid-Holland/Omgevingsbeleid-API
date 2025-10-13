import logging
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from app.api.domains.users.services.security import Security
from app.api.domains.werkingsgebieden.repositories import SqliteGeometryRepository, SqliteAreaGeometryRepository
from app.core.settings import Settings
from app.main import app
from app.tests.fixtures.database_fixtures import DatabaseFixtures


@pytest.fixture(scope="session")
def settings():
    return Settings()

@pytest.fixture(scope="session")
def engine(settings):
    engine = create_engine(
        settings.SQLALCHEMY_TEST_DATABASE_URI,
        connect_args={"check_same_thread": False},
        future=True,
    )
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.enable_load_extension(True)
    return engine

@pytest.fixture(scope="session")
def db_session(engine):
    connection = engine.connect()
    TestSession = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = TestSession()
    session.execute(text("SELECT load_extension('mod_spatialite')"))
    yield session

@pytest.fixture(scope="session")
def tables(engine, db_session):
    from app.core.db.base import Base
    Base.metadata.create_all(bind=engine)
    yield
    db_session.execute(text("PRAGMA foreign_keys = OFF"))
    Base.metadata.drop_all(bind=engine)
    db_session.close()

@pytest.fixture(scope="session")
def fixtures(engine, settings, db_session):
    _ = engine.connect()
    db_session.execute(text("PRAGMA foreign_keys = OFF"))

    geo_repo = SqliteGeometryRepository()
    area_repo = SqliteAreaGeometryRepository()
    sec = Security(settings.SECRET_KEY, timedelta(days=5))
    df = DatabaseFixtures(db_session, geo_repo, area_repo, sec)
    df.create_all()
    db_session.close()

@pytest.fixture
def db_session_transaction(engine, tables, fixtures, settings, db_session):
    connection = engine.connect()
    db_session.execute(text("PRAGMA foreign_keys = ON")) # Turn on foreign keys after loading fixtures
    transaction = connection.begin()
    _ = connection.begin_nested()

    @event.listens_for(db_session, "after_transaction_end")
    def restart_savepoint(session_, transaction_):
        if transaction_.nested and not transaction_.conn.closed:
            session_.connection().begin_nested()

    yield db_session
    db_session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session_transaction):
    app.dependency_overrides = {}
    app.state.db_sessionmaker = sessionmaker(bind=db_session_transaction.bind)

    with TestClient(app) as test_client:
        yield test_client
    db_session_transaction.close()

@pytest.fixture
def test_super_user():
    return {"username": "test@example.com", "password": "password", "grant_type": "password"}

@pytest.fixture
def test_super_user_access_auth_header(client, test_super_user):
    login_response = client.post("/login/access-token", data=test_super_user)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
