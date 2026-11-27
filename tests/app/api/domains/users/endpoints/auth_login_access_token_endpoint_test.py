import httpx2
import pytest

from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import DEFAULT_PASSWORD, UserSpec
from tests.fixtures.internal.types import Ref


async def test_login_returns_a_token_for_the_user(client: httpx2.AsyncClient, ctx: Context):
    admin = ctx.f.find(Ref(UserSpec, "admin")).spec

    response = await client.post("/login/access-token", data={"username": admin.email, "password": DEFAULT_PASSWORD})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["identifier"]["id"] == str(admin.id)

    user = await client.get(f"/users/{admin.id}", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert user.status_code == 200, user.text


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("admin@pzh.nl", "wrong-password", id="wrong-password"),
        pytest.param("nobody@pzh.nl", DEFAULT_PASSWORD, id="unknown-user"),
    ],
)
async def test_login_rejects_bad_credentials(client: httpx2.AsyncClient, username: str, password: str):
    response = await client.post("/login/access-token", data={"username": username, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
