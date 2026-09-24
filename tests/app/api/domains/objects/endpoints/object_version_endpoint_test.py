from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BaseObjectSpec, BeleidsdoelSpec, GebiedSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, ref",
    [
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"), id="latest-version"),
        # Retrievable by UUID regardless of validity window.
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_3_future"), id="future-version"),
        pytest.param("/maatregelen", Ref(MaatregelSpec, "maatregel_6_past_end_validity"), id="past-end-validity"),
    ],
)
def test_returns_the_requested_version_by_uuid(client: TestClient, ctx: Context, prefix: str, ref: Ref):
    expected: BaseObjectSpec = ctx.f.find(ref).spec

    response = client.get(f"{prefix}/version/{expected.UUID}")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["UUID"] == str(expected.UUID)
    assert body["Code"] == expected.Code


def test_version_is_scoped_to_object_type(client: TestClient, ctx: Context):
    # A maatregel UUID must not resolve under the beleidsdoel routes.
    maatregel: MaatregelSpec = ctx.f.find(Ref(MaatregelSpec, "maatregel_6_past_end_validity")).spec

    response = client.get(f"/beleidsdoelen/version/{maatregel.UUID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "object_uuid does not exist"


def test_unknown_uuid_returns_404(client: TestClient):
    response = client.get("/beleidsdoelen/version/00000000-0000-0000-0000-00000000dead")

    assert response.status_code == 404
    assert response.json()["detail"] == "object_uuid does not exist"


def test_response_matches_the_full_model_shape(client: TestClient, ctx: Context):
    expected: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid")).spec
    model: type[BaseModel] = ctx.m.get_pydantic_model("beleidsdoel_full")

    body: dict = client.get(f"/beleidsdoelen/version/{expected.UUID}").json()

    assert set(body.keys()) == set(model.model_fields)


@pytest.mark.parametrize(
    "url_prefix, object_ref, user, expected_gebied_refs",
    [
        pytest.param(
            "/maatregelen/version",
            Ref(MaatregelSpec, "maatregel_6_initial"),
            "client",
            [Ref(GebiedSpec, "nature_west_v1"), Ref(GebiedSpec, "nature_east_v1")],
            id="vigerend-non-auth",
        ),
    ],
)
def test_gebiedsaanwijzingen_from_text(
    request: FixtureRequest, ctx: Context, url_prefix: str, object_ref: Ref, user: str, expected_gebied_refs: list[Ref]
):
    client: TestClient = request.getfixturevalue(user)
    source_object: MaatregelSpec = ctx.f.find(object_ref).spec
    expected_gebied_uuids: set[str] = {str(ctx.f.primary_key_uuid(gebied_key)) for gebied_key in expected_gebied_refs}

    url = f"{url_prefix}/{source_object.UUID}"
    response = client.get(url)
    assert response.status_code == 200

    body: dict = response.json()
    gebieden_uuids: set[UUID] = {gebied["UUID"] for gebied in body.get("Gebiedsaanwijzingen_Gebieden", [])}

    assert gebieden_uuids == expected_gebied_uuids
