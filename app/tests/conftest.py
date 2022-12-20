from datetime import datetime
from typing import Dict
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import sessionmaker

from app import models, schemas
from app.api.deps import get_db
from app.core.config import settings
from app.db.base_class import NULL_UUID, metadata
from app.tests.utils.data_loader import FixtureLoader
from app.tests.utils.exceptions import SetupMethodException
from app.tests.utils.headers import get_admin_headers, get_fred_headers
from app.tests.utils.mock_data import generate_data
from main import create_app

# Overwrite DB url to test DB - method should be dep injected
def get_test_db():
    engine = create_engine(settings.SQLALCHEMY_TEST_DATABASE_URI, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()


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
    app = create_app()
    # Ensures calls to test client use a test db session
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def admin_headers(client: TestClient) -> Dict[str, str]:
    return get_admin_headers(client)


@pytest.fixture(scope="module")
def fred_headers(client: TestClient) -> Dict[str, str]:
    return get_fred_headers(client)


@pytest.fixture(scope="function")
def add_modifiable_objects(db: Session):
    """
    Genericly add some entities to the DB before every test.
    Yields the full list of DB objects to use for before/after checks
    """
    ENTITIES = [
        (models.Ambitie, schemas.AmbitieCreate),
        (models.Belang, schemas.BelangCreate),
        (models.Beleidskeuze, schemas.BeleidskeuzeCreate),
    ]

    # Build patchable objects
    to_create = list()
    uuid_map = dict()
    for model, schema in ENTITIES:
        request_data = generate_data(
            obj_schema=schema,
            default_str="automated test",
        )

        obj_data = schema(**request_data).dict()

        request_time = datetime.now()
        uuid = uuid4()

        obj_data["UUID"] = uuid
        obj_data["Created_By_UUID"] = NULL_UUID
        obj_data["Modified_By_UUID"] = NULL_UUID
        obj_data["Created_Date"] = request_time
        obj_data["Modified_Date"] = request_time

        instance = model(**obj_data)
        to_create.append(instance)
        ent_name = str(model.__table__).lower()
        uuid_map[ent_name] = uuid

    try:
        for item in to_create:
            db.add(item)
        db.commit()

        db_objects = list()
        for model, schema in ENTITIES:
            ent_name = str(model.__table__).lower()
            db_objects.append(
                db.query(model).filter(model.UUID == uuid_map[ent_name]).one()
            )

        yield db_objects
    except Exception:
        raise SetupMethodException
