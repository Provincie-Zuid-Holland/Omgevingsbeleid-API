import uuid

import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient

from app.core.tables.modules import ModuleTable
from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def test_edits_module_fields(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = admin.post(
        "/modules/1",
        json={"Title": "An edited title", "Description": "An edited description"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    module = ctx.session.get(ModuleTable, 1)
    assert module
    assert module.Title == "An edited title"
    assert module.Description == "An edited description"
    assert module.Modified_By_UUID == admin_uuid


def test_partial_update_leaves_other_fields_untouched(admin: TestClient, ctx: Context):
    original_description: str = ctx.f.find(Ref(ModuleSpec, "module_1")).spec.Description

    response = admin.post("/modules/1", json={"Title": "Only the title changes"})

    assert response.status_code == 200, response.text
    module = ctx.session.get(ModuleTable, 1)
    assert module
    assert module.Title == "Only the title changes"
    assert module.Description == original_description


def test_can_lock_module(admin: TestClient, ctx: Context):
    response = admin.post("/modules/1", json={"Temporary_Locked": True})

    assert response.status_code == 200, response.text
    module = ctx.session.get(ModuleTable, 1)
    assert module
    assert module.Temporary_Locked is True


def test_can_change_module_manager(admin: TestClient, ctx: Context):
    new_manager: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post("/modules/1", json={"Module_Manager_1_UUID": str(new_manager)})

    assert response.status_code == 200, response.text
    module = ctx.session.get(ModuleTable, 1)
    assert module
    assert module.Module_Manager_1_UUID == new_manager


def test_empty_body_returns_400(admin: TestClient):
    response = admin.post("/modules/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Nothing to update"


def test_duplicate_managers_returns_400(admin: TestClient, ctx: Context):
    manager: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))

    response = admin.post(
        "/modules/1",
        json={"Module_Manager_1_UUID": str(manager), "Module_Manager_2_UUID": str(manager)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Duplicate manager"


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"Title": "ab"}, id="title-too-short"),
        pytest.param({"Description": "ab"}, id="description-too-short"),
        pytest.param({"Module_Manager_1_UUID": "not-a-uuid"}, id="manager-1-not-a-uuid"),
    ],
)
def test_invalid_body_returns_422(admin: TestClient, body: dict):
    response = admin.post("/modules/1", json=body)

    assert response.status_code == 422, response.text


def test_closed_module_returns_404(admin: TestClient):
    response = admin.post("/modules/3", json={"Title": "Cannot edit a closed module"})

    assert response.status_code == 404
    assert response.json()["detail"] == "De module is gesloten"


def test_unknown_module_returns_404(admin: TestClient):
    response = admin.post("/modules/999999", json={"Title": "No such module"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Module niet gevonden"


def test_module_manager_without_role_permission_can_edit(ambtenaar: TestClient, ctx: Context):
    # The ambtenaar role lacks module_can_edit_module, but is manager of module 4,
    # so the manager whitelist grants access.
    response = ambtenaar.post("/modules/4", json={"Title": "Edited by the manager"})

    assert response.status_code == 200, response.text
    module = ctx.session.get(ModuleTable, 4)
    assert module
    assert module.Title == "Edited by the manager"


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("admin", 200, None, id="user-with-permission"),
    ],
)
def test_permission_matrix(request: FixtureRequest, client_fixture: str, expected_status: int, expected_detail: str):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    # Module 2 is not managed by the ambtenaar, so the whitelist does not apply here.
    response = test_client.post("/modules/2", json={"Title": "A new title for module 2"})

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
