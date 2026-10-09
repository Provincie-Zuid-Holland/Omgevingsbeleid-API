import uuid

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest
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

    response = admin.post("/beleidsdoel/static/1", json={"portfolio_holder_1_id": str(viewer)})

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"
    assert _beleidsdoel_static(ctx.session).portfolio_holder_1_id == viewer


def test_edit_writes_a_changelog_entry(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    admin.post("/beleidsdoel/static/1", json={"portfolio_holder_1_id": str(viewer)})

    change_log = ctx.session.scalar(
        select(ChangeLogTable)
        .where(ChangeLogTable.action_type == "edit_object_static")
        .order_by(desc(ChangeLogTable.created_date))
    )
    assert change_log is not None
    assert change_log.object_type == "beleidsdoel"
    assert change_log.object_id == 1
    assert change_log.created_by_id == admin_uuid


def test_empty_body_returns_400(admin: TestClient):
    response = admin.post("/beleidsdoel/static/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Nothing to update"


def test_unknown_lineage_returns_404(admin: TestClient, ctx: Context):
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/beleidsdoel/static/999", json={"portfolio_holder_1_id": str(viewer)})

    assert response.status_code == 404
    assert response.json()["detail"] == "lineage_id does not exist"


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param(["owner_1_id", "owner_2_id"], id="owner-1-and-owner-2"),
        pytest.param(["owner_1_id", "owner_3_id"], id="owner-1-and-owner-3"),
        pytest.param(["owner_2_id", "owner_3_id"], id="owner-2-and-owner-3"),
        pytest.param(["owner_1_id", "owner_2_id", "owner_3_id"], id="all-three-owners"),
    ],
)
def test_duplicate_owners_returns_422(admin: TestClient, ctx: Context, fields: list[str]):
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))
    response = admin.post("/beleidsdoel/static/1", json={f: str(viewer) for f in fields})

    assert response.status_code == 422, response.text
    assert "Owners should vary" in response.text


def test_empty_owner_2_or_3_is_allowed(admin: TestClient, ctx: Context):
    response = admin.post(
        "/beleidsdoel/static/1",
        json={"owner_2_id": None, "owner_3_id": None},
    )
    assert response.status_code == 200, response.text


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("viewer", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("owner_1", 200, None, id="owner-1-via-whitelist"),
        pytest.param("owner_3", 200, None, id="owner-3-via-whitelist"),
        pytest.param("admin", 200, None, id="role-with-permission"),
    ],
)
def test_edit_permission_matrix(
    request: FixtureRequest, ctx: Context, client_fixture: str, expected_status: int, expected_detail: str
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    viewer: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = test_client.post("/beleidsdoel/static/1", json={"portfolio_holder_1_id": str(viewer)})

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail


def test_owner_1_required_returns_422(admin: TestClient, ctx: Context):
    response = admin.post(
        "/beleidsdoel/static/1",
        json={"owner_1_id": None},
    )

    assert response.status_code == 422
    assert "Missing required value" in response.text
