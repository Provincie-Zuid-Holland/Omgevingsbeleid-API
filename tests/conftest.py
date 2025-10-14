import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastapi import Request

from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.users import UsersTable
from app.main import app


@pytest.fixture()
def mock_db_session():
    session = MagicMock(spec=Session)
    yield session


@pytest.fixture()
def mock_db_sessionmaker(mock_db_session):
    sessionmaker_mock = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = mock_db_session
    context_manager.__exit__.return_value = None
    sessionmaker_mock.begin.return_value = context_manager
    return sessionmaker_mock


@pytest.fixture(autouse=True)
def override_db_dependency(mock_db_sessionmaker):
    from app.api.dependencies import depends_db_session

    def _override_depends_db_session(request: Request):
        db_sessionmaker = mock_db_sessionmaker
        with db_sessionmaker.begin() as session:
            yield session

    app.dependency_overrides[depends_db_session] = _override_depends_db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


fake_user = UsersTable(
    UUID="11111111-0000-0000-0000-000000000001",
    Gebruikersnaam="admin",
    Email="test@example.com",
    Rol="Superuser",
    Status="Actief",
)


@pytest.fixture(autouse=True)
def override_auth_dependency():
    def fake_get_current_user():
        return fake_user

    app.dependency_overrides[depends_current_user] = fake_get_current_user
    yield
    app.dependency_overrides.pop(depends_current_user, None)


def mock_select_result(session, return_value):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = return_value
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result
