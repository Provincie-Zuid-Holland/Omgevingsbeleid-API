from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleSpec
from tests.fixtures.internal.types import Ref


def test_returns_the_module(admin: TestClient, ctx: Context):
    module_id = 1
    module = ctx.f.find(Ref(ModuleSpec, f"module_{module_id}")).spec

    response = admin.get(f"/modules/{module_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module"]["module_id"] == module.module_id
    assert body["module"]["created_by_id"] == str(module.created_by_id)
    assert body["module"]["modified_by_id"] == str(module.modified_by_id)
    assert body["module"]["activated"] == module.activated
    assert body["module"]["closed"] == module.closed
    assert body["module"]["successful"] == module.successful
    assert body["module"]["temporary_locked"] == module.temporary_locked
    assert body["module"]["title"] == module.title
    assert body["module"]["description"] == module.description
    assert body["module"]["module_manager_1_id"] == str(module.module_manager_1_id)
    assert body["module"]["module_manager_2_id"] == module.module_manager_2_id  # None
    assert body["module"]["status"]["status"] == "Ter Inzage"
    assert [s["status"] for s in body["status_history"]] == ["Niet-Actief", "Ontwerp GS Concept", "Ter Inzage"]


def test_returns_a_closed_module(admin: TestClient):
    response = admin.get("/modules/3")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module"]["closed"] is True
    assert body["module"]["status"]["status"] == "Gesloten"
    assert [s["status"] for s in body["status_history"]] == ["Niet-Actief", "Ontwerp GS Concept", "Gesloten"]


def test_returns_a_module_that_is_not_activated(admin: TestClient):
    response = admin.get("/modules/2")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module"]["activated"] is False
    assert [s["status"] for s in body["status_history"]] == ["Niet-Actief"]


def test_unknown_module_returns_404(admin: TestClient):
    response = admin.get("/modules/999999")

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Module niet gevonden"
