import uuid

from fastapi.testclient import TestClient

from app.api.domains.modules.types import ModuleStatusCode
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def test_lists_all_statuses_of_the_module(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    module_id = 1

    response = admin.get(f"/modules/{module_id}/status")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == [
        {
            "id": 1,
            "module_id": module_id,
            "status": "Niet-Actief",
            "created_date": "2025-06-01T00:00:00",
            "created_by_id": str(admin_uuid),
        },
        {
            "id": 2,
            "module_id": module_id,
            "status": "Ontwerp GS Concept",
            "created_date": "2025-06-01T01:00:00",
            "created_by_id": str(admin_uuid),
        },
        {
            "id": 3,
            "module_id": module_id,
            "status": "Ter Inzage",
            "created_date": "2025-06-01T04:00:00",
            "created_by_id": str(admin_uuid),
        },
    ]


def test_lists_the_new_status_after_patching(admin: TestClient):
    response = admin.get("/modules/7/status")
    body = response.json()
    assert len(body) == 2

    response = admin.patch("/modules/7/status", json={"status": "Ontwerp GS"})
    assert response.status_code == 200, response.text

    response = admin.get("/modules/7/status")

    assert response.status_code == 200, response.text
    body = response.json()
    assert [s["status"] for s in body] == [
        "Niet-Actief",
        "Ontwerp GS Concept",
        "Ontwerp GS",
    ]
