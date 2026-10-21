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


def test_creates_atemporal_object(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    beheerder_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "beheerder"))
    response = admin.post(
        "/verplicht-programma",
        json={
            "title": "New verplicht programma - title",
            "description": "New verplicht programma - description",
            "object_statics": {
                "owner_1_id": str(admin_uuid),
                "owner_2_id": str(beheerder_uuid),
            },
        },
    )

    verplicht_programma = _get_object(ctx.session, "verplicht_programma", 2)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(verplicht_programma.id)
    assert body["object_id"] == 2
    assert verplicht_programma.title == "New verplicht programma - title"
    assert verplicht_programma.description == "New verplicht programma - description"
