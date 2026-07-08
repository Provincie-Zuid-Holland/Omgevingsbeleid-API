from typing import Optional
import uuid

import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, MaatregelSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _object_uuid(ctx: Context, spec_type, key: str) -> uuid.UUID:
    return ctx.f.primary_key_uuid(Ref(spec_type, key))


def _payload(object_uuid: uuid.UUID, action: str = "Edit", explanation: str = "", conclusion: str = "") -> dict:
    return {
        "Object_UUID": str(object_uuid),
        "Action": action,
        "Explanation": explanation,
        "Conclusion": conclusion,
    }


def _context(session: Session, module_id: int, object_id: int) -> ModuleObjectContextTable:
    module_context: Optional[ModuleObjectContextTable] = session.scalars(
        select(ModuleObjectContextTable)
        .where(ModuleObjectContextTable.Module_ID == module_id)
        .where(ModuleObjectContextTable.Object_Type == "beleidsdoel")
        .where(ModuleObjectContextTable.Object_ID == object_id)
    ).first()
    assert module_context
    return module_context


def _drafts(session: Session, module_id: int, object_id: int) -> list[ModuleObjectsTable]:
    return list(
        session.scalars(
            select(ModuleObjectsTable)
            .where(ModuleObjectsTable.Module_ID == module_id)
            .where(ModuleObjectsTable.Object_ID == object_id)
        )
    )


@pytest.mark.parametrize(
    "object_key, object_id, action",
    [
        pytest.param("beleidsdoel_2_latest_valid", 2, "Edit", id="edit"),
        pytest.param("beleidsdoel_3_latest_valid", 3, "Terminate", id="terminate"),
    ],
)
def test_adds_existing_object_creates_context_and_draft(
    admin: TestClient, ctx: Context, object_key: str, object_id: int, action: str
):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, object_key)

    response = admin.post(
        "/modules/2/add-existing-object",
        json=_payload(object_uuid, action=action, explanation="Why", conclusion="Outcome"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    context = _context(ctx.session, 2, object_id)
    assert context.Hidden is False
    assert context.Action == action
    assert context.Original_Adjust_On == object_uuid
    assert context.Explanation == "Why"
    assert context.Conclusion == "Outcome"
    assert context.Created_By_UUID == admin_uuid

    drafts = _drafts(ctx.session, 2, object_id)
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.Module_ID == 2
    assert draft.Adjust_On == object_uuid
    assert draft.UUID != object_uuid
    assert draft.Modified_By_UUID == admin_uuid


def test_readding_hidden_object_unhides_and_updates_context(admin: TestClient, ctx: Context):
    # Module 1 tracks beleidsdoel object 1 (Action=Edit). Hide it to simulate a removed object,
    # then re-add it as Terminate. The existing context must be un-hidden and rewritten in place.
    context = _context(ctx.session, 1, 1)
    assert context
    assert context.Action == "Edit"
    context.Hidden = True
    ctx.session.flush()

    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, "beleidsdoel_1_latest_valid")
    response = admin.post("/modules/1/add-existing-object", json=_payload(object_uuid, action="Terminate"))

    assert response.status_code == 200, response.text

    ctx.session.expire_all()
    refreshed = _context(ctx.session, 1, 1)
    assert refreshed
    assert refreshed.Hidden is False
    assert refreshed.Action == "Terminate"
    assert refreshed.Original_Adjust_On == object_uuid


def test_unknown_object_uuid_returns_400(admin: TestClient):
    response = admin.post(
        "/modules/2/add-existing-object",
        json=_payload(uuid.UUID("00000000-0000-0000-0000-000000000000")),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown object for uuid"


def test_object_type_not_allowed_returns_400(admin: TestClient, ctx: Context):
    # maatregel is intentionally excluded from this endpoint's allowed_object_types.
    object_uuid: uuid.UUID = _object_uuid(ctx, MaatregelSpec, "maatregel_1_latest_valid")

    response = admin.post("/modules/2/add-existing-object", json=_payload(object_uuid))

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid Object_Type")


def test_object_already_in_module_returns_400(admin: TestClient, ctx: Context):
    # Module 1 already tracks beleidsdoel object 1 (a non-hidden context).
    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, "beleidsdoel_1_latest_valid")

    response = admin.post("/modules/1/add-existing-object", json=_payload(object_uuid))

    assert response.status_code == 400
    assert response.json()["detail"] == "Object already exists in module"


def test_locked_module_returns_400(admin: TestClient, ctx: Context):
    module = ctx.session.get(ModuleTable, 2)
    assert module
    module.Temporary_Locked = True
    ctx.session.flush()

    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, "beleidsdoel_2_latest_valid")
    response = admin.post("/modules/2/add-existing-object", json=_payload(object_uuid))

    assert response.status_code == 400
    assert response.json()["detail"] == "The module is locked"


@pytest.mark.parametrize(
    "module_id, detail",
    [
        pytest.param(3, "De module is gesloten", id="closed"),
        pytest.param(999999, "Module niet gevonden", id="unknown"),
    ],
)
def test_inaccessible_module_returns_404(admin: TestClient, ctx: Context, module_id: int, detail: str):
    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, "beleidsdoel_2_latest_valid")
    response = admin.post(f"/modules/{module_id}/add-existing-object", json=_payload(object_uuid))

    assert response.status_code == 404
    assert response.json()["detail"] == detail


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("viewer", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("ambtenaar", 200, None, id="role-with-permission"),
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
    object_uuid: uuid.UUID = _object_uuid(ctx, BeleidsdoelSpec, "beleidsdoel_2_latest_valid")

    response = test_client.post("/modules/2/add-existing-object", json=_payload(object_uuid))

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
