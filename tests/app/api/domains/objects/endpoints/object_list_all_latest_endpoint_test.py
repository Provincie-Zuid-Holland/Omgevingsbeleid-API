import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def test_lists_latest_valid_version_per_lineage(client: TestClient):
    response = client.get("/objects/valid")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["total"] == 13
    assert len(body["results"]) == 13

    first = body["results"][0]
    assert set(first.keys()) == {"Object_Type", "ObjectStatics", "Model"}
    # Every lineage resolves to its March version.
    for r in body["results"]:
        assert r["Model"]["Modified_Date"].startswith("2025-03-01")


@pytest.mark.parametrize(
    "object_types, expected_total",
    [
        pytest.param(["maatregel"], 6, id="maatregel"),
        pytest.param(["beleidsdoel"], 3, id="beleidsdoel"),
        pytest.param(["beleidsdoel", "beleidskeuze"], 7, id="beleidsdoel+beleidskeuze"),
    ],
)
def test_object_types_filter(client: TestClient, object_types: list[str], expected_total: int):
    query = "&".join(f"object_types={t}" for t in object_types)
    body = client.get(f"/objects/valid?{query}").json()
    assert body["total"] == expected_total
    assert {r["Object_Type"] for r in body["results"]} == set(object_types)


def test_unknown_object_type_returns_400(client: TestClient):
    response = client.get("/objects/valid?object_types=invalid")
    assert response.status_code == 400
    assert "Invalid object type" in response.json()["detail"]


def test_pagination_limits_results_but_not_total(client: TestClient):
    body = client.get("/objects/valid?limit=5&offset=0").json()
    assert body["total"] == 13
    assert body["limit"] == 5
    assert len(body["results"]) == 5

    last_page = client.get("/objects/valid?limit=5&offset=10").json()
    assert last_page["offset"] == 10
    assert len(last_page["results"]) == 3


@pytest.mark.parametrize(
    "sort_order, reverse",
    [
        pytest.param("ASC", False, id="asc"),
        pytest.param("DESC", True, id="desc"),
    ],
)
def test_sort_by_object_id(client: TestClient, sort_order: str, reverse: bool):
    body = client.get(f"/objects/valid?sort_column=Object_ID&sort_order={sort_order}").json()
    ids = [r["Model"]["Object_ID"] for r in body["results"]]
    assert ids == sorted(ids, reverse=reverse)


def test_future_validity_version_is_skipped(client: TestClient):
    # beleidsdoel-3 has a newer 2099 version; the March one must win.
    body = client.get("/objects/valid?object_types=beleidsdoel").json()
    bd3 = next(r for r in body["results"] if r["Model"]["Object_ID"] == 3)
    assert bd3["Model"]["Title"] == "Beleidsdoel 3 from march"
    assert bd3["Model"]["Modified_Date"].startswith("2025-03-01")


def test_past_end_validity_is_still_returned(client: TestClient):
    body = client.get("/objects/valid?object_types=maatregel").json()
    m6 = next(r for r in body["results"] if r["Model"]["Object_ID"] == 6)
    assert m6["Model"]["End_Validity"].startswith("2025-06-01")


def test_owner_uuid_filters_across_static_owner_columns(client: TestClient, ctx: Context):
    owner_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner-1"))
    body = client.get(f"/objects/valid?owner_uuid={owner_uuid}").json()
    found_results = sorted((r["Object_Type"], r["Model"]["Object_ID"]) for r in body["results"])

    assert body["total"] == 3
    assert found_results == [("beleidsdoel", 1), ("beleidskeuze", 1), ("maatregel", 1)]


def test_owner_uuid_without_matches_returns_empty(client: TestClient):
    unknown = uuid.UUID("00000000-0000-0000-0000-00000000dead")
    body = client.get(f"/objects/valid?owner_uuid={unknown}").json()
    assert body["total"] == 0
    assert body["results"] == []
