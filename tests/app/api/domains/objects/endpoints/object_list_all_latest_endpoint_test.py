import uuid

import httpx2
import pytest

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, MaatregelSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


async def test_lists_latest_valid_version_per_lineage(client: httpx2.AsyncClient):
    response = await client.get("/objects/valid")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["total"] == 22
    assert len(body["results"]) == 20

    first = body["results"][0]
    assert set(first.keys()) == {"object_type", "object_statics", "model"}


@pytest.mark.parametrize(
    "object_types, expected_total",
    [
        pytest.param(["maatregel"], 6, id="maatregel"),
        pytest.param(["beleidsdoel"], 3, id="beleidsdoel"),
        pytest.param(["beleidsdoel", "beleidskeuze"], 7, id="beleidsdoel+beleidskeuze"),
    ],
)
async def test_object_types_filter(client: httpx2.AsyncClient, object_types: list[str], expected_total: int):
    query = "&".join(f"object_types={t}" for t in object_types)
    body = (await client.get(f"/objects/valid?{query}")).json()
    assert body["total"] == expected_total
    assert {r["object_type"] for r in body["results"]} == set(object_types)


async def test_unknown_object_type_returns_400(client: httpx2.AsyncClient):
    response = await client.get("/objects/valid?object_types=invalid")
    assert response.status_code == 400
    assert "Invalid object type" in response.json()["detail"]


async def test_pagination_limits_results_but_not_total(client: httpx2.AsyncClient):
    body = (await client.get("/objects/valid?limit=5&offset=0")).json()
    assert body["total"] == 22
    assert body["limit"] == 5
    assert len(body["results"]) == 5

    last_page = (await client.get("/objects/valid?limit=5&offset=20")).json()
    assert last_page["offset"] == 20
    assert len(last_page["results"]) == 2


@pytest.mark.parametrize(
    "sort_order, reverse",
    [
        pytest.param("ASC", False, id="asc"),
        pytest.param("DESC", True, id="desc"),
    ],
)
async def test_sort_by_object_id(client: httpx2.AsyncClient, sort_order: str, reverse: bool):
    body = (await client.get(f"/objects/valid?sort_column=object_id&sort_order={sort_order}")).json()
    ids = [r["model"]["object_id"] for r in body["results"]]
    assert ids == sorted(ids, reverse=reverse)


async def test_future_validity_version_is_skipped(client: httpx2.AsyncClient, ctx: Context):
    # beleidsdoel-3 has a newer 2099 version; the latest valid (March) one must win.
    expected = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_3_latest_valid")).spec
    body = (await client.get("/objects/valid?object_types=beleidsdoel")).json()
    bd3 = next(r for r in body["results"] if r["model"]["object_id"] == 3)
    assert bd3["model"]["id"] == str(expected.id)


async def test_past_end_validity_is_still_returned(client: httpx2.AsyncClient, ctx: Context):
    expected = ctx.f.find(Ref(MaatregelSpec, "maatregel_6_past_end_validity")).spec
    body = (await client.get("/objects/valid?object_types=maatregel")).json()
    m6 = next(r for r in body["results"] if r["model"]["object_id"] == 6)
    assert m6["model"]["id"] == str(expected.id)


async def test_owner_uuid_filters_across_static_owner_columns(client: httpx2.AsyncClient, ctx: Context):
    owner_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "owner_1"))
    body = (await client.get(f"/objects/valid?owner_id={owner_id}")).json()
    found_results = sorted((r["object_type"], r["model"]["object_id"]) for r in body["results"])

    assert body["total"] == 3
    assert found_results == [("beleidsdoel", 1), ("beleidskeuze", 1), ("maatregel", 1)]


async def test_owner_uuid_without_matches_returns_empty(client: httpx2.AsyncClient):
    unknown = uuid.UUID("00000000-0000-0000-0000-00000000dead")
    body = (await client.get(f"/objects/valid?owner_id={unknown}")).json()
    assert body["total"] == 0
    assert body["results"] == []
