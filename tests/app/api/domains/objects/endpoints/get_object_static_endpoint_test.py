import uuid

from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def test_returns_object_static(admin: TestClient, ctx: Context):
    owner_1_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner_1"))
    owner_3_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner_3"))

    response = admin.get("/beleidsdoel/static/1")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner_1"]["id"] == str(owner_1_id)
    assert body["owner_2"] is None
    assert body["owner_3"]["id"] == str(owner_3_id)


def test_returns_object_static_not_found(admin: TestClient, ctx: Context):
    response = admin.get("/beleidsdoel/static/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Object static niet gevonden"
