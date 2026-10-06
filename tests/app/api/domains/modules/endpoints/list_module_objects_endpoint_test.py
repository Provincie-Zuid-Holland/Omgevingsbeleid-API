import uuid

from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def test_lists_latest_module_objects_all(beheerder: TestClient, ctx: Context):
    response = beheerder.get("/modules/objects/latest")

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["module_id"] for r in body["results"]} == {1, 5, 6, 7, 8}


def test_lists_latest_module_objects_per_module_id(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 1},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {
        "beleidsdoel-1",
        "beleidsdoel-2",
        "beleidsdoel-4",
        "maatregel-6",
    }


def test_lists_latest_module_objects_per_module_id_object_type(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 6, "object_types": ["gebied"]},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {"gebied-1", "gebied-610"}


def test_lists_latest_module_objects_per_module_id_owner_id_mine(beheerder: TestClient, ctx: Context):
    owner_1_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner_1"))

    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 5, "owner_id": str(owner_1_uuid), "owner_type": "Mine"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {"beleidskeuze-510"}


def test_lists_latest_module_objects_per_module_id_owner_id_others(beheerder: TestClient, ctx: Context):
    owner_1_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner_1"))

    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 5, "owner_id": str(owner_1_uuid), "owner_type": "Others"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {
        "beleidskeuze-1",
        "gebied-1",
        "gebied-510",
        "gebiedengroep-510",
        "gebiedsaanwijzing-1",
        "gebiedsaanwijzing-510",
        "maatregel-1",
        "maatregel-6",
    }


def test_lists_latest_module_objects_per_module_id_owner_id_unknown(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 5, "owner_type": "Mine"},
    )

    assert response.status_code == 400, response.text
    body: dict[str, str] = response.json()
    assert body["detail"] == "owner_id is required when owner_type is 'Mine' or 'Others'"


def test_lists_latest_module_objects_per_module_id_owner_type_unknown(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 5, "owner_type": "unknown"},
    )

    assert response.status_code == 422, response.text
    body: dict[str, str] = response.json()
    assert body["detail"][0]["msg"] == "Input should be 'All', 'Mine' or 'Others'"


def test_lists_latest_module_objects_per_minimum_status(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"minimum_status": "Ter Inzage"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {
        "beleidsdoel-1",
        "beleidsdoel-2",
        "beleidsdoel-4",
        "beleidsdoel-8",
        "beleidskeuze-8",
        "beleidskeuze-9",
        "maatregel-6",
    }


def test_lists_latest_module_objects_per_active(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"only_active_modules": "false"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["module_id"] for r in body["results"]} == {1, 3, 5, 6, 7, 8}


def test_lists_latest_module_objects_per_title(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"module_id": 6, "title": "Gebiedengroep"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["model"]["code"] for r in body["results"]} == {"gebiedengroep-610"}


def test_lists_latest_module_objects_per_actions(beheerder: TestClient, ctx: Context):
    response = beheerder.get(
        "/modules/objects/latest",
        params={"actions": "Terminate"},
    )

    assert response.status_code == 200, response.text
    body: dict[str, str] = response.json()
    assert {r["module_id"] for r in body["results"]} == {5, 8}
    assert {r["model"]["code"] for r in body["results"]} == {"beleidskeuze-9", "gebied-1"}
