import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_beleidskeuze_spec import ModuleBeleidskeuzeSpec
from tests.fixtures.internal.types import Ref, Spec


@pytest.mark.parametrize(
    "spec_type, spec_key, module_id, object_id, object_type",
    [
        pytest.param(
            ModuleBeleidsdoelSpec,
            "mod_1_beleidsdoel_1_third_entry",
            1,
            1,
            "beleidsdoel",
            id="latest-version-of-the-lineage",
        ),
        pytest.param(
            ModuleBeleidskeuzeSpec,
            "mod_5_beleidskeuze_510_first_entry",
            5,
            510,
            "beleidskeuze",
            id="lineage-that-only-exists-in-the-module",
        ),
    ],
)
def test(
    admin: TestClient,
    ctx: Context,
    spec_type: type[Spec],
    spec_key: str,
    module_id: int,
    object_id: int,
    object_type: str,
):
    expected_object = ctx.f.find(Ref(spec_type, spec_key)).spec

    response = admin.get(f"/modules/{module_id}/object/{object_type}/latest/{object_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(expected_object.id)
    assert body["object_id"] == expected_object.object_id
    assert body["code"] == expected_object.code
    assert body["title"] == expected_object.title
    assert body["description"] == expected_object.description


def test_unknown_lineage_returns_400(admin: TestClient):
    response = admin.get("/modules/5/object/beleidsdoel/latest/1")

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "lineage_id does not exist"
