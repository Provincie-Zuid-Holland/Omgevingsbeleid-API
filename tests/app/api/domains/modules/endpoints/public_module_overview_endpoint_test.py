import pytest
from fastapi.testclient import TestClient

from app.api.domains.modules.types import ModuleStatusCode
from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.types import Ref


def test_returns_the_objects_as_they_were_at_the_public_status(client: TestClient, ctx: Context):
    # The third entry of beleidsdoel-1 and beleidsdoel-2 were added after the Ter Inzage status
    beleidsdoel_1: ModuleBeleidsdoelSpec = ctx.f.find(
        Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_second_entry")
    ).spec
    beleidsdoel_4: ModuleBeleidsdoelSpec = ctx.f.find(
        Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_4_first_entry")
    ).spec

    response = client.get("/revisions/1")

    assert response.status_code == 200, response.text

    module = response.json()["module"]
    assert module["module_id"] == 1
    assert module["title"] == "Title of Module 1"
    assert module["description"] == "Description of Module 1"
    assert module["status"]["status"] == ModuleStatusCode.Ter_Inzage.value

    objects = response.json()["objects"]

    assert objects[0]["id"] == str(beleidsdoel_1.id)
    assert objects[0]["title"] == beleidsdoel_1.title
    assert objects[0]["module_object_context"]["action"] == "Edit"
    assert objects[1]["id"] == str(beleidsdoel_4.id)
    assert objects[1]["title"] == beleidsdoel_4.title
    assert objects[1]["module_object_context"]["action"] == "Create"

    assert {o["module_id"] for o in objects} == {1}
    assert {o["object_type"] for o in objects} == {"beleidsdoel"}


@pytest.mark.parametrize(
    "module_id",
    [
        pytest.param(5, id="status-ontwerp-gs-concept"),
        pytest.param(2, id="status-niet-actief"),
    ],
)
def test_non_public_status_returns_400(client: TestClient, module_id: int):
    response = client.get(f"/revisions/{module_id}")

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Invalid status for module"


@pytest.mark.parametrize(
    "module_id, expected_detail",
    [
        pytest.param(3, "De module is gesloten", id="closed-module"),
        pytest.param(999999, "Module niet gevonden", id="unknown-module"),
    ],
)
def test_unavailable_module_returns_404(client: TestClient, module_id: int, expected_detail: str):
    response = client.get(f"/revisions/{module_id}")

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == expected_detail
