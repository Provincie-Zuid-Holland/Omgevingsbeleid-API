import pytest
from fastapi.testclient import TestClient

from app.api.domains.users.types import User
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("user_key", ["admin", "ambtenaar", "viewer"])
def test_returns_the_requested_user(admin: TestClient, ctx: Context, user_key: str):
    expected: UserSpec = ctx.f.find(Ref(UserSpec, user_key)).spec

    body = admin.get(f"/users/{expected.UUID}").json()

    assert body["UUID"] == str(expected.UUID)
    assert body["Email"] == expected.Email
    assert body["Rol"] == expected.Rol
    assert body["Gebruikersnaam"] == expected.Gebruikersnaam


def test_any_authenticated_user_can_fetch_a_user(ambtenaar: TestClient, ctx: Context):
    target: UserSpec = ctx.f.find(Ref(UserSpec, "admin")).spec

    response = ambtenaar.get(f"/users/{target.UUID}")

    assert response.status_code == 200, response.text
    assert response.json()["UUID"] == str(target.UUID)


def test_response_matches_the_user_model_shape(admin: TestClient, ctx: Context):
    target: UserSpec = ctx.f.find(Ref(UserSpec, "admin")).spec

    body: dict = admin.get(f"/users/{target.UUID}").json()

    assert set(body.keys()) == set(User.model_fields)


def test_unknown_uuid_returns_400(admin: TestClient):
    response = admin.get("/users/00000000-0000-0000-0000-0000000000aa")

    assert response.status_code == 400
    assert response.json()["detail"] == "User does not exist"


def test_unauthenticated_returns_401(client: TestClient, ctx: Context):
    target: UserSpec = ctx.f.find(Ref(UserSpec, "admin")).spec

    response = client.get(f"/users/{target.UUID}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
