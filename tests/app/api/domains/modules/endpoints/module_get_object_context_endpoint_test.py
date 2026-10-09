import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleBeleidskeuzeSpec
from tests.fixtures.internal.types import Ref


def test_returns_the_object_context(admin: TestClient, ctx: Context):
    first_entry: ModuleBeleidskeuzeSpec = ctx.f.find(
        Ref(ModuleBeleidskeuzeSpec, "mod_5_beleidskeuze_510_first_entry")
    ).spec

    response = admin.get("/modules/5/object-context/beleidskeuze/510")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module_id"] == 5
    assert body["object_type"] == first_entry.object_type
    assert body["object_id"] == first_entry.object_id
    assert body["code"] == first_entry.code
    assert body["action"] == "Create"
    assert body["explanation"] == first_entry.context_explanation
    assert body["conclusion"] == first_entry.context_conclusion
    assert body["original_adjust_on"] == "None" or str(first_entry.adjust_on)
    assert body["created_by"]["id"] == str(first_entry.created_by_id)
    assert body["modified_by"]["id"] == str(first_entry.modified_by_id)


@pytest.mark.parametrize(
    "module_id, object_type, object_id, detail",
    [
        pytest.param(1, "unknown", 1, "Object context niet gevonden", id="context-unknown"),
        pytest.param(5, "gebied", 511, "Object context is verwijderd", id="context-hidden"),
    ],
)
def test_doesnt_find_context(
    admin: TestClient, ctx: Context, module_id: int, object_type: str, object_id: str, detail: str
):
    response = admin.get(f"/modules/{module_id}/object-context/{object_type}/{object_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == detail
