import uuid

import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.others import ChangeLogTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _beleidsdoel_static(session: Session, lineage_id: int = 1) -> ObjectStaticsTable:
    return ObjectStaticRepository().get_by_object_type_and_id(session, "beleidsdoel", lineage_id)


def test_edit_updates_the_static_row(admin: TestClient, ctx: Context):
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/beleidsdoel/static/1", json={"Portfolio_Holder_1_UUID": str(viewer)})

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"
    assert _beleidsdoel_static(ctx.session).Portfolio_Holder_1_UUID == viewer


def test_edit_writes_a_changelog_entry(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    admin.post("/beleidsdoel/static/1", json={"Portfolio_Holder_1_UUID": str(viewer)})

    change_log = ctx.session.scalar(
        select(ChangeLogTable)
        .where(ChangeLogTable.Action_Type == "edit_object_static")
        .order_by(desc(ChangeLogTable.Created_Date))
    )
    assert change_log is not None
    assert change_log.Object_Type == "beleidsdoel"
    assert change_log.Object_ID == 1
    assert change_log.Created_By_UUID == admin_uuid


def test_empty_body_returns_400(admin: TestClient):
    response = admin.post("/beleidsdoel/static/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Nothing to update"


def test_unknown_lineage_returns_404(admin: TestClient, ctx: Context):
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/beleidsdoel/static/999", json={"Portfolio_Holder_1_UUID": str(viewer)})

    assert response.status_code == 404
    assert response.json()["detail"] == "lineage_id does not exist"


def test_duplicate_owners_returns_422(admin: TestClient, ctx: Context):
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post(
        "/beleidsdoel/static/1",
        json={"Owner_1_UUID": str(viewer), "Owner_2_UUID": str(viewer)},
    )

    assert response.status_code == 422
    assert "Owners should vary" in response.text


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("owner_1", 200, None, id="owner-via-whitelist"),
        pytest.param("admin", 200, None, id="role-with-permission"),
    ],
)
def test_edit_permission_matrix(
    request: FixtureRequest, ctx: Context, client_fixture: str, expected_status: int, expected_detail: str
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = test_client.post("/beleidsdoel/static/1", json={"Portfolio_Holder_1_UUID": str(viewer)})

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
