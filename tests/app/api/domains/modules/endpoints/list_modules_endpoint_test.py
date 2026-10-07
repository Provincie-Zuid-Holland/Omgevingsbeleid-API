import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.types import Ref


def test_lists_all_modules_last_created_first(admin: TestClient):
    response = admin.get("/modules")

    assert response.status_code == 200, response.text
    body = response.json()
    assert [m["module_id"] for m in body["results"]] == [8, 7, 6, 5, 4, 3, 2, 1]


def test_returns_the_module_fields(admin: TestClient, ctx: Context):
    expected_module: ModuleSpec = ctx.f.find(Ref(ModuleSpec, "module_1")).spec

    response = admin.get("/modules", params={"filter_title": expected_module.title})

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["results"]) == 1
    module = body["results"][0]
    assert module["module_id"] == expected_module.module_id
    assert module["title"] == expected_module.title
    assert module["description"] == expected_module.description
    assert module["activated"] == expected_module.activated
    assert module["closed"] == expected_module.closed
    assert module["successful"] == expected_module.successful
    assert module["temporary_locked"] == expected_module.temporary_locked
    assert module["module_manager_1_id"] == str(expected_module.module_manager_1_id)


@pytest.mark.parametrize(
    "params, expected_module_ids",
    [
        pytest.param({"filter_activated": "true"}, [8, 7, 6, 5, 4, 3, 1], id="activated"),
        pytest.param({"filter_activated": "false"}, [2], id="not-activated"),
        pytest.param({"filter_closed": "true"}, [3], id="closed"),
        pytest.param({"filter_closed": "false"}, [8, 7, 6, 5, 4, 2, 1], id="not-closed"),
        pytest.param({"filter_successful": "true"}, [], id="successful"),
        pytest.param({"filter_successful": "false"}, [8, 7, 6, 5, 4, 3, 2, 1], id="not-successful"),
        pytest.param({"filter_title": "Title of Module 5"}, [5], id="title-exact"),
        pytest.param({"filter_title": "%Module 1%"}, [1], id="title-like-pattern"),
        pytest.param({"filter_title": "Module"}, [], id="title-without-wildcards"),
        pytest.param({"filter_activated": "true", "filter_closed": "false"}, [8, 7, 6, 5, 4, 1], id="combined"),
    ],
)
def test_filters_modules(admin: TestClient, params: dict[str, str], expected_module_ids: list[int]):
    response = admin.get("/modules", params=params)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == len(expected_module_ids)
    assert [m["module_id"] for m in body["results"]] == expected_module_ids


@pytest.mark.parametrize(
    "client_fixture, expected_module_ids",
    [
        pytest.param("owner_1", [5, 1], id="owner-of-module-objects"),
        pytest.param("manager_of_module_4", [4], id="module-manager"),
    ],
)
def test_filters_on_only_mine(request: FixtureRequest, client_fixture: str, expected_module_ids: list[int]):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    response = test_client.get("/modules", params={"only_mine": "true"})

    assert response.status_code == 200, response.text
    assert [m["module_id"] for m in response.json()["results"]] == expected_module_ids


@pytest.mark.parametrize(
    "object_type, lineage_id, expected_module_ids",
    [
        pytest.param("beleidsdoel", 1, [1], id="beleidsdoel-1"),
        pytest.param("gebied", 1, [6, 5], id="gebied-1"),
        pytest.param("beleidsdoel", 999999, [], id="unknown-lineage"),
    ],
)
def test_filters_on_object_code(admin: TestClient, object_type: str, lineage_id: int, expected_module_ids: list[int]):
    response = admin.get("/modules", params={"object_type": object_type, "lineage_id": lineage_id})

    assert response.status_code == 200, response.text
    assert [m["module_id"] for m in response.json()["results"]] == expected_module_ids
