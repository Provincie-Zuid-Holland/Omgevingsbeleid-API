import uuid
from typing import Optional

import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import ModuleStatusCodeInternal
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _statuses(session: Session, module_id: int) -> list[ModuleStatusHistoryTable]:
    return list(
        session.scalars(select(ModuleStatusHistoryTable).where(ModuleStatusHistoryTable.Module_ID == module_id))
    )


def _payload(
    manager_1: uuid.UUID,
    manager_2: Optional[uuid.UUID] = None,
    title: str = "A brand new module",
    description: str = "Description of the new module",
) -> dict:
    body: dict = {
        "Title": title,
        "Description": description,
        "Module_Manager_1_UUID": str(manager_1),
    }
    if manager_2 is not None:
        body["Module_Manager_2_UUID"] = str(manager_2)
    return body


def test_creates_a_module(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))
    manager_2: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "ambtenaar"))

    response = admin.post("/modules", json=_payload(manager_1, manager_2))

    assert response.status_code == 200, response.text
    module_id: int = response.json()["Module_ID"]

    module = ctx.session.get(ModuleTable, module_id)
    assert module
    assert module.Title == "A brand new module"
    assert module.Description == "Description of the new module"
    assert module.Module_Manager_1_UUID == manager_1
    assert module.Module_Manager_2_UUID == manager_2
    assert module.Activated is False
    assert module.Closed is False
    assert module.Successful is False
    assert module.Temporary_Locked is False
    assert module.Created_By_UUID == admin_uuid
    assert module.Modified_By_UUID == admin_uuid


def test_creates_an_initial_niet_actief_status(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/modules", json=_payload(manager_1))

    assert response.status_code == 200, response.text
    module_id: int = response.json()["Module_ID"]

    statuses = _statuses(ctx.session, module_id)
    assert len(statuses) == 1
    assert statuses[0].Status == ModuleStatusCodeInternal.Niet_Actief
    assert statuses[0].Created_By_UUID == admin_uuid


def test_creates_a_module_without_second_manager(admin: TestClient, ctx: Context):
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/modules", json=_payload(manager_1))

    assert response.status_code == 200, response.text
    module = ctx.session.get(ModuleTable, response.json()["Module_ID"])
    assert module
    assert module.Module_Manager_2_UUID is None


def test_duplicate_managers_returns_400(admin: TestClient, ctx: Context):
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/modules", json=_payload(manager_1, manager_1))

    assert response.status_code == 400
    assert response.json()["detail"] == "Duplicate manager"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"Title": "ab"}, id="title-too-short"),
        pytest.param({"Description": "ab"}, id="description-too-short"),
        pytest.param({"Module_Manager_1_UUID": None}, id="missing-manager-1"),
        pytest.param({"Module_Manager_1_UUID": "not-a-uuid"}, id="manager-1-not-a-uuid"),
    ],
)
def test_invalid_body_returns_422(admin: TestClient, ctx: Context, overrides: dict):
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))
    body: dict = _payload(manager_1)
    for key, value in overrides.items():
        if value is None:
            body.pop(key, None)
        else:
            body[key] = value

    response = admin.post("/modules", json=body)

    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("admin", 200, None, id="user-with-permission"),
    ],
)
def test_permission_matrix(
    request: FixtureRequest,
    ctx: Context,
    client_fixture: str,
    expected_status: int,
    expected_detail: str,
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    manager_1: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = test_client.post("/modules", json=_payload(manager_1))

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
