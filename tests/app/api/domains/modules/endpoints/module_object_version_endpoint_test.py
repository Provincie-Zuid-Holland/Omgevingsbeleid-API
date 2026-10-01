import uuid

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_beleidskeuze_spec import ModuleBeleidskeuzeSpec
from tests.fixtures.internal.spec.modules.module_gebied_spec import ModuleGebiedSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "key",
    [
        pytest.param("mod_1_beleidsdoel_1_first_entry", id="first-version"),
        pytest.param("mod_1_beleidsdoel_1_second_entry", id="middle-version"),
        pytest.param("mod_1_beleidsdoel_1_third_entry", id="latest-version"),
    ],
)
def test_returns_the_requested_version(admin: TestClient, ctx: Context, key: str):
    record = ctx.f.find(Ref(ModuleBeleidsdoelSpec, key))
    expected_object: ModuleBeleidsdoelSpec = record.spec

    response = admin.get(f"/modules/1/object/beleidsdoel/version/{expected_object.id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(expected_object.id)
    assert body["code"] == "beleidsdoel-1"
    assert body["title"] == expected_object.title


def test_unknown_module_returns_404(admin: TestClient, ctx: Context):
    object_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_first_entry"))

    response = admin.get(f"/modules/999999/object/beleidsdoel/version/{object_uuid}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Module niet gevonden"


@pytest.mark.parametrize(
    "path, ref",
    [
        pytest.param("/modules/1/object/beleidsdoel/version", None, id="unknown-uuid"),
        pytest.param(
            "/modules/5/object/beleidsdoel/version",
            Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_first_entry"),
            id="object-of-other-module",
        ),
        pytest.param(
            "/modules/5/object/beleidsdoel/version",
            Ref(ModuleBeleidskeuzeSpec, "mod_5_beleidskeuze_510_first_entry"),
            id="object-of-other-type",
        ),
    ],
)
def test_unknown_module_object_returns_404(admin: TestClient, ctx: Context, path: str, ref: Ref | None):
    object_uuid: uuid.UUID = ctx.f.primary_key_uuid(ref) if ref else uuid.uuid4()

    response = admin.get(f"{path}/{object_uuid}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Module Object niet gevonden"


def test_hidden_module_object_returns_404(admin: TestClient, ctx: Context):
    object_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(ModuleGebiedSpec, "mod_5_gebied_511"))

    response = admin.get(f"/modules/5/object/gebied/version/{object_uuid}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Module Object Context is verwijderd"


def test_requires_authentication(client: TestClient, ctx: Context):
    object_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_first_entry"))

    response = client.get(f"/modules/1/object/beleidsdoel/version/{object_uuid}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "client_fixture, module_id, ref, expected_status, expected_detail",
    [
        pytest.param(
            "client",
            1,
            Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_first_entry"),
            200,
            None,
            id="anonymous-module-past-minimum-status",
        ),
        pytest.param(
            "client",
            2,
            None,
            401,
            "module objects lacks the minimum status for view.",
            id="anonymous-module-below-minimum-status",
        ),
        pytest.param(
            "admin",
            2,
            None,
            404,
            "Module Object niet gevonden",
            id="authenticated-module-below-minimum-status",
        ),
    ],
)
def test_revisions_minimum_status(
    request: FixtureRequest,
    ctx: Context,
    client_fixture: str,
    module_id: int,
    ref: Ref | None,
    expected_status: int,
    expected_detail: str | None,
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    object_uuid: uuid.UUID = ctx.f.primary_key_uuid(ref) if ref else uuid.uuid4()

    response = test_client.get(f"/revisions/{module_id}/beleidsdoel/version/{object_uuid}")

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
