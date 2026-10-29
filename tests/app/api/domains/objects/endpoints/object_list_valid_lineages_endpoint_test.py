import httpx2
import pytest
from pydantic import BaseModel

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BaseObjectSpec, BeleidsdoelSpec, BeleidskeuzeSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, ref",
    [
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"), id="beleidsdoel"),
        pytest.param("/beleidskeuzes", Ref(BeleidskeuzeSpec, "beleidskeuze_1_latest_valid"), id="beleidskeuze"),
        pytest.param("/maatregelen", Ref(MaatregelSpec, "maatregel_1_latest_valid"), id="maatregel"),
    ],
)
async def test_lineage_resolves_to_latest_valid_version(
    client: httpx2.AsyncClient, ctx: Context, prefix: str, ref: Ref
):
    expected: BaseObjectSpec = ctx.f.find(ref).spec

    results = {r["code"]: r for r in (await client.get(f"{prefix}/valid")).json()["results"]}

    assert results[expected.code]["id"] == str(expected.id)


async def test_lineage_with_past_end_validity_is_excluded(client: httpx2.AsyncClient, ctx: Context):
    expired: MaatregelSpec = ctx.f.find(Ref(MaatregelSpec, "maatregel_6_past_end_validity")).spec

    codes = {r["code"] for r in (await client.get("/maatregelen/valid")).json()["results"]}

    assert expired.code not in codes


async def test_future_only_version_is_skipped(client: httpx2.AsyncClient, ctx: Context):
    # beleidsdoel-3 has a 2099 version; the latest *valid* version must win.
    expected: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_3_latest_valid")).spec

    results = {r["code"]: r for r in (await client.get("/beleidsdoelen/valid")).json()["results"]}

    assert results[expected.code]["id"] == str(expected.id)


@pytest.mark.parametrize(
    "prefix, object_type",
    [
        pytest.param("/beleidsdoelen", "beleidsdoel", id="beleidsdoel"),
        pytest.param("/beleidskeuzes", "beleidskeuze", id="beleidskeuze"),
        pytest.param("/maatregelen", "maatregel", id="maatregel"),
    ],
)
async def test_only_returns_lineages_of_its_object_type(client: httpx2.AsyncClient, prefix: str, object_type: str):
    results = (await client.get(f"{prefix}/valid")).json()["results"]

    assert results, "expected at least one lineage to assert scoping against"
    assert all(r["code"].startswith(f"{object_type}-") for r in results)


@pytest.mark.parametrize(
    "make_filter, should_match",
    [
        pytest.param(lambda title: title, True, id="exact-match"),
        pytest.param(lambda title: title.lower(), True, id="case-insensitive"),
        pytest.param(lambda title: title[:-2] + "%", True, id="wildcard-prefix"),
        pytest.param(lambda title: title[:-2], False, id="no-wildcard-is-not-a-substring"),
    ],
)
async def test_filter_title_uses_sql_like(client: httpx2.AsyncClient, ctx: Context, make_filter, should_match: bool):
    expected = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid")).spec

    body = (await client.get("/beleidsdoelen/valid", params={"filter_title": make_filter(expected.title)})).json()
    codes = {r["code"] for r in body["results"]}

    assert (expected.code in codes) is should_match


async def test_filter_title_without_matches_returns_empty(client: httpx2.AsyncClient):
    body = (await client.get("/beleidsdoelen/valid", params={"filter_title": "no lineage has this title"})).json()

    assert body["total"] == 0
    assert body["results"] == []


async def test_pagination_caps_page_size_without_changing_total(client: httpx2.AsyncClient):
    total = (await client.get("/maatregelen/valid")).json()["total"]

    page = (await client.get("/maatregelen/valid?limit=2&offset=0")).json()

    assert page["total"] == total
    assert page["limit"] == 2
    assert len(page["results"]) == 2


async def test_offset_returns_a_disjoint_page(client: httpx2.AsyncClient):
    first = (await client.get("/maatregelen/valid?limit=2&offset=0&sort_column=object_id&sort_order=ASC")).json()
    second = (await client.get("/maatregelen/valid?limit=2&offset=2&sort_column=object_id&sort_order=ASC")).json()

    assert second["offset"] == 2
    first_codes = {r["code"] for r in first["results"]}
    second_codes = {r["code"] for r in second["results"]}
    assert first_codes.isdisjoint(second_codes)


async def test_default_sort_is_title_ascending(client: httpx2.AsyncClient):
    titles = [r["title"] for r in (await client.get("/maatregelen/valid")).json()["results"]]

    assert titles == sorted(titles)


@pytest.mark.parametrize(
    "sort_order, reverse",
    [
        pytest.param("ASC", False, id="asc"),
        pytest.param("DESC", True, id="desc"),
    ],
)
async def test_sort_by_object_id(client: httpx2.AsyncClient, sort_order: str, reverse: bool):
    body = (await client.get(f"/maatregelen/valid?sort_column=object_id&sort_order={sort_order}")).json()
    ids = [r["object_id"] for r in body["results"]]

    assert ids == sorted(ids, reverse=reverse)


async def test_invalid_sort_column_returns_400(client: httpx2.AsyncClient):
    response = await client.get("/beleidsdoelen/valid?sort_column=Nope")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid sort column"


async def test_result_matches_the_response_model_shape(client: httpx2.AsyncClient, ctx: Context):
    expected: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid")).spec
    model: type[BaseModel] = ctx.m.get_pydantic_model("beleidsdoel_basic")

    row: dict[str, dict] = {r["code"]: r for r in (await client.get("/beleidsdoelen/valid")).json()["results"]}[
        expected.code
    ]

    assert set(row.keys()) == set(model.model_fields)
    # No later valid version exists for this lineage, so the enrichment yields None.
    assert row["next_version"] is None
