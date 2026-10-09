import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.objects import ObjectsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _get_object(session: Session, object_type: str, object_id: int) -> ObjectsTable:
    object_result = session.scalar(select(ObjectsTable).filter(ObjectsTable.code == f"{object_type}-{object_id}"))
    assert object_result
    return object_result


def test_edits_atemporal_object(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    beheerder_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "beheerder"))
    response = admin.post(
        "/verplicht-programma/1",
        json={
            "title": "Edit verplicht programma - title",
            "description": "Edit verplicht programma - description",
            "object_statics": {
                "owner_1_id": str(admin_uuid),
                "owner_2_id": str(beheerder_uuid),
            },
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    verplicht_programma = _get_object(ctx.session, "verplicht_programma", 1)
    assert verplicht_programma.title == "Edit verplicht programma - title"
    assert verplicht_programma.description == "Edit verplicht programma - description"
    assert verplicht_programma.modified_by_id == admin_uuid
    assert verplicht_programma.object_statics.cached_title == "Edit verplicht programma - title"


def test_edits_atemporal_object_object_not_existing(admin: TestClient, ctx: Context):
    response = admin.post("/verplicht-programma/9999", json={})

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Object not found"


def test_edits_atemporal_object_no_updates(admin: TestClient, ctx: Context):
    response = admin.post("/verplicht-programma/1", json={})

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Nothing to update"
