from typing import Dict

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import sessionmaker

from app.db.base_class import metadata
#from app.db.session import SessionLocal
from app.core.config import settings
from app.tests.utils.data_loader import FixtureLoader
from app.tests.utils.headers import get_admin_headers, get_fred_headers
from main import app


@pytest.fixture(scope="class")
def db():
    engine = create_engine(settings.SQLALCHEMY_TEST_DATABASE_URI, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()


@pytest.fixture(scope="class")
def fixture_data(db: Session):
    engine = db.get_bind()
    metadata.drop_all(bind=engine)
    metadata.create_all(bind=engine)

    loader = FixtureLoader(db)
    loader.load_fixtures()

    yield loader


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_headers(client: TestClient) -> Dict[str, str]:
    return get_admin_headers(client)


@pytest.fixture(scope="module")
def fred_headers(client: TestClient) -> Dict[str, str]:
    return get_fred_headers(client)
