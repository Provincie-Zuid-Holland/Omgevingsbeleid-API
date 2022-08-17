from typing import Dict
import asyncio  # noqa

import pytest
import pytest_asyncio  # noqa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base_class import metadata
from app.db.session import SessionLocal
from app.tests.utils.utils import get_admin_headers, get_fred_headers
from app.tests.utils.data_loader import FixtureLoader
from main import app


# # This is for async setup, not really useful with mssql
# @pytest.fixture
# def event_loop():
#     loop = asyncio.get_event_loop()
#     yield loop
#     loop.close()
#
#
# @pytest.fixture
# def non_mocked_hosts() -> List[str]:
#     return ["test"]
#
#
# @pytest.fixture
# async def client() -> AsyncClient:
#     async with AsyncClient(app=app, base_url="http://test") as client:
#         yield client


@pytest.fixture(scope="class")
def db() -> Session:
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
