import uuid
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _payload(
    owner_id: uuid.UUID, owner_id_2: uuid.UUID | None = None, object_type: str = "beleidsdoel"
) -> dict[str, str]:
    payload: dict[str, str] = {
        "object_type": object_type,
        "title": f"New {object_type}",
        "owner_1_id": str(owner_id),
        "client_1_id": str(owner_id),
        "explanation": f"New {object_type} explanation",
        "conclusion": f"New {object_type} conclusion",
    }
    if owner_id_2:
        payload["owner_2_id"] = str(owner_id_2)
    return payload


def test_adds_new_module_object(beheerder: TestClient, ctx: Context):
    beheerder_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "beheerder"))
    ambtenaar_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "ambtenaar"))

    module_id: int = 2
    payload = _payload(owner_id=beheerder_id, owner_id_2=ambtenaar_id)
    response = beheerder.post(
        f"/modules/{module_id}/add-new-object",
        json=payload,
    )
    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert body["object_type"] == "beleidsdoel"
    assert type(body["object_id"]) == int
    code: str = f"beleidsdoel-{body['object_id']}"
    assert body["code"] == code

    stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.code == code)
    object_statics: ObjectStaticsTable | None = ctx.session.scalars(stmt).first()
    assert object_statics
    assert object_statics.object_type == payload["object_type"]
    assert object_statics.object_id == body["object_id"]
    assert object_statics.owner_1_id == uuid.UUID(payload["owner_1_id"])
    assert object_statics.owner_2_id == uuid.UUID(payload["owner_2_id"])
    assert object_statics.client_1_id == uuid.UUID(payload["client_1_id"])
    assert object_statics.cached_title == payload["title"]

    stmt = (
        select(ModuleObjectContextTable)
        .filter(ModuleObjectContextTable.module_id == module_id)
        .filter(ModuleObjectContextTable.code == code)
    )
    module_object_context: ModuleObjectContextTable | None = ctx.session.scalars(stmt).first()
    assert module_object_context
    assert module_object_context.original_adjust_on is None
    assert module_object_context.hidden == False
    assert module_object_context.action == ModuleObjectActionFull.Create
    assert module_object_context.explanation == payload["explanation"]
    assert module_object_context.conclusion == payload["conclusion"]
    assert module_object_context.created_by.id == beheerder_id
    assert module_object_context.modified_by.id == beheerder_id

    stmt = (
        select(ModuleObjectsTable)
        .filter(ModuleObjectsTable.module_id == module_id)
        .filter(ModuleObjectsTable.code == code)
    )
    module_object: ModuleObjectsTable | None = ctx.session.scalars(stmt).first()
    assert module_object
    assert module_object.object_type == payload["object_type"]
    assert module_object.object_id == body["object_id"]
    assert module_object.title == payload["title"]


def test_adds_new_module_object_duplicate_owner(beheerder: TestClient, ctx: Context):
    beheerder_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "beheerder"))
    payload = _payload(owner_id=beheerder_id, owner_id_2=beheerder_id)
    response = beheerder.post(
        "/modules/2/add-new-object",
        json=payload,
    )
    assert response.status_code == 422, response.text
    body: dict[str, str] = response.json()
    assert body["detail"][0]["msg"].__contains__("Duplicate owner")


@dataclass
class ModuleNewObjectGuardCase:
    object_type: str
    response_code: int
    module_id: int
    response_detail: str


@pytest.mark.parametrize(
    "case",
    [
        ModuleNewObjectGuardCase(
            object_type="forbidden_type", response_code=400, module_id=2, response_detail="Invalid object_type"
        ),
        ModuleNewObjectGuardCase(
            object_type="beleidsdoel", response_code=404, module_id=3, response_detail="De module is gesloten"
        ),
        ModuleNewObjectGuardCase(
            object_type="beleidsdoel", response_code=400, module_id=7, response_detail="The module is locked"
        ),
    ],
)
def test_adds_new_module_object_guards(beheerder: TestClient, ctx: Context, case: ModuleNewObjectGuardCase):
    beheerder_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "beheerder"))
    payload = _payload(owner_id=beheerder_id, object_type=case.object_type)
    response = beheerder.post(
        f"/modules/{case.module_id}/add-new-object",
        json=payload,
    )
    assert response.status_code == case.response_code, response.text
    body: dict[str, str] = response.json()
    assert body["detail"].__contains__(case.response_detail)
