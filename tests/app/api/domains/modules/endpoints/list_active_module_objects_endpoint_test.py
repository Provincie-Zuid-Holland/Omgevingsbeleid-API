import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

from app.api.domains.modules.types import ModuleObjectActionFull, ModuleStatusCode
from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_gebied_spec import ModuleGebiedSpec
from tests.fixtures.internal.types import Ref


def test_returns_the_latest_module_object_of_the_lineage(admin: TestClient, ctx: Context):
    expected_module_object: ModuleBeleidsdoelSpec = ctx.f.find(
        Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_third_entry")
    ).spec

    response = admin.get("/modules/object/beleidsdoel/active/1?minimum_status=Ontwerp GS Concept")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["module"]["module_id"] == 1
    assert item["module"]["title"] == "Title of Module 1"
    assert item["module"]["closed"] is False
    assert item["module"]["status"]["status"] == ModuleStatusCode.Ter_Inzage.value
    assert item["module_object"]["id"] == str(expected_module_object.id)
    assert item["module_object"]["module_id"] == expected_module_object.module_id
    assert item["module_object"]["title"] == expected_module_object.title
    assert item["action"] == ModuleObjectActionFull.Edit.value


def test_returns_the_context_action_of_the_module_object(admin: TestClient, ctx: Context):
    expected_module_object_mod_5: ModuleGebiedSpec = ctx.f.find(Ref(ModuleGebiedSpec, "mod_5_gebied_1")).spec
    expected_module_object_mod_6: ModuleGebiedSpec = ctx.f.find(Ref(ModuleGebiedSpec, "nature_west_v1_mod_6")).spec

    response = admin.get("/modules/object/gebied/active/1?minimum_status=Ontwerp GS Concept")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    item = body[0]
    assert item["module_object"]["id"] == str(expected_module_object_mod_6.id)
    assert item["action"] == "Edit"
    item = body[1]
    assert item["module_object"]["id"] == str(expected_module_object_mod_5.id)
    assert item["action"] == "Terminate"


@pytest.mark.parametrize(
    "minimum_status, expected_module_ids",
    [
        pytest.param("Ontwerp GS Concept", [1], id="status-before-module-status"),
        pytest.param("Ter Inzage", [1], id="status-equal-to-module-status"),
        pytest.param("Definitief ontwerp GS", [], id="status-after-module-status"),
    ],
)
def test_filters_on_minimum_status_of_the_module(
    admin: TestClient, minimum_status: str, expected_module_ids: list[int]
):
    response = admin.get(f"/modules/object/beleidsdoel/active/1?minimum_status={minimum_status}")

    assert response.status_code == 200, response.text
    assert [item["module"]["module_id"] for item in response.json()] == expected_module_ids


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/modules/object/beleidsdoel/active/5", id="closed-module"),
        pytest.param("/modules/object/gebied/active/511", id="hidden-module-object"),
        pytest.param("/modules/object/gebied/active/3", id="terminated-and-hidden-module-object"),
        pytest.param("/modules/object/beleidsdoel/active/999999", id="unknown-lineage"),
        pytest.param("/modules/object/beleidsdoel/active/3", id="lineage-not-in-any-module"),
    ],
)
def test_returns_empty_list_when_no_active_module_object_exists(admin: TestClient, path: str):
    response = admin.get(f"{path}?minimum_status=Ontwerp GS Concept")

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_only_returns_module_objects_of_the_requested_object_type(admin: TestClient):
    response = admin.get("/modules/object/gebiedengroep/active/510?minimum_status=Ontwerp GS Concept")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["module_object"]["title"] == "Gebiedengroep 510 in Module 5"


def test_rejects_unknown_minimum_status(admin: TestClient):
    response = admin.get("/modules/object/beleidsdoel/active/1", params={"minimum_status": "Unknown"})

    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    "client_fixture, expected_status",
    [
        pytest.param("client", 401, id="unauthenticated"),
        pytest.param("viewer", 200, id="any-authenticated-user"),
        pytest.param("ambtenaar", 200, id="ambtenaar"),
        pytest.param("admin", 200, id="admin"),
    ],
)
def test_list_permission_matrix(request: FixtureRequest, client_fixture: str, expected_status: int):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    response = test_client.get("/modules/object/beleidsdoel/active/1?minimum_status=Ontwerp GS Concept")

    assert response.status_code == expected_status, response.text
