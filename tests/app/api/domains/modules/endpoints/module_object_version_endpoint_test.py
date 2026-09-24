from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleGebiedSpec, ModuleMaatregelSpec
from tests.fixtures.internal.spec.objects import GebiedSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "url_prefix, object_ref, user, expected_gebied_refs",
    [
        pytest.param(
            "/modules/1/object/maatregel/version",
            Ref(ModuleMaatregelSpec, "maatregel_6_mod_1"),
            "admin",
            [Ref(GebiedSpec, "nature_west_v1"), Ref(GebiedSpec, "nature_east_v1")],
            id="module-with-same-gebied",
        ),
        pytest.param(
            "/modules/5/object/maatregel/version",
            Ref(ModuleMaatregelSpec, "maatregel_6_mod_5"),
            "admin",
            [Ref(GebiedSpec, "nature_south_v1")],
            id="module-with-different-target",
        ),
        pytest.param(
            "/modules/6/object/maatregel/version",
            Ref(ModuleMaatregelSpec, "maatregel_6_mod_6"),
            "admin",
            [Ref(ModuleGebiedSpec, "nature_west_v1_mod_6"), Ref(GebiedSpec, "nature_east_v1")],
            id="module-with-newer-version-of-target",
        ),
    ],
)
def module_test_gebiedsaanwijzingen_from_text(
    request: FixtureRequest, ctx: Context, url_prefix: str, object_ref: Ref, user: str, expected_gebied_refs: list[Ref]
):
    client: TestClient = request.getfixturevalue(user)
    source_object: MaatregelSpec = ctx.f.find(object_ref).spec
    expected_gebied_uuids: set[str] = {str(ctx.f.primary_key_uuid(gebied_key)) for gebied_key in expected_gebied_refs}

    url: str = f"{url_prefix}/{source_object.UUID}"
    response = client.get(url)
    assert response.status_code == 200

    body: dict = response.json()
    gebieden_uuids: set[UUID] = {gebied["UUID"] for gebied in body.get("Gebiedsaanwijzingen_Gebieden", [])}

    assert gebieden_uuids == expected_gebied_uuids
