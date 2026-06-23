from typing import Dict, Type

from pydantic import BaseModel
import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, BeleidskeuzeSpec, MaatregelSpec, BaseObjectSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, ref",
    [
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"), id="beleidsdoel"),
        pytest.param("/beleidskeuzes", Ref(BeleidskeuzeSpec, "beleidskeuze_1_latest_valid"), id="beleidskeuze"),
        pytest.param("/maatregelen", Ref(MaatregelSpec, "maatregel_1_latest_valid"), id="maatregel"),
    ],
)
def test_lineage_resolves_to_latest_valid_version(client: TestClient, ctx: Context, prefix: str, ref: Ref):
    expected: BaseObjectSpec = ctx.f.find(ref).spec

    results = {r["Code"]: r for r in client.get(f"{prefix}/valid").json()["results"]}

    assert results[expected.Code]["UUID"] == str(expected.UUID)


def test_lineage_with_past_end_validity_is_excluded(client: TestClient, ctx: Context):
    expired: MaatregelSpec = ctx.f.find(Ref(MaatregelSpec, "maatregel_6_past_end_validity")).spec

    codes = {r["Code"] for r in client.get("/maatregelen/valid").json()["results"]}

    assert expired.Code not in codes


def test_future_only_version_is_skipped(client: TestClient, ctx: Context):
    # beleidsdoel-3 has a 2099 version; the latest *valid* version must win.
    expected: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_3_latest_valid")).spec

    results = {r["Code"]: r for r in client.get("/beleidsdoelen/valid").json()["results"]}

    assert results[expected.Code]["UUID"] == str(expected.UUID)


@pytest.mark.parametrize(
    "prefix, object_type",
    [
        pytest.param("/beleidsdoelen", "beleidsdoel", id="beleidsdoel"),
        pytest.param("/beleidskeuzes", "beleidskeuze", id="beleidskeuze"),
        pytest.param("/maatregelen", "maatregel", id="maatregel"),
    ],
)
def test_only_returns_lineages_of_its_object_type(client: TestClient, prefix: str, object_type: str):
    results = client.get(f"{prefix}/valid").json()["results"]

    assert results, "expected at least one lineage to assert scoping against"
    assert all(r["Code"].startswith(f"{object_type}-") for r in results)


@pytest.mark.parametrize(
    "make_filter, should_match",
    [
        pytest.param(lambda title: title, True, id="exact-match"),
        pytest.param(lambda title: title.lower(), True, id="case-insensitive"),
        pytest.param(lambda title: title[:-2] + "%", True, id="wildcard-prefix"),
        pytest.param(lambda title: title[:-2], False, id="no-wildcard-is-not-a-substring"),
    ],
)
def test_filter_title_uses_sql_like(client: TestClient, ctx: Context, make_filter, should_match: bool):
    expected = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid")).spec

    body = client.get("/beleidsdoelen/valid", params={"filter_title": make_filter(expected.Title)}).json()
    codes = {r["Code"] for r in body["results"]}

    assert (expected.Code in codes) is should_match


def test_filter_title_without_matches_returns_empty(client: TestClient):
    body = client.get("/beleidsdoelen/valid", params={"filter_title": "no lineage has this title"}).json()

    assert body["total"] == 0
    assert body["results"] == []


def test_pagination_caps_page_size_without_changing_total(client: TestClient):
    total = client.get("/maatregelen/valid").json()["total"]

    page = client.get("/maatregelen/valid?limit=2&offset=0").json()

    assert page["total"] == total
    assert page["limit"] == 2
    assert len(page["results"]) == 2


def test_offset_returns_a_disjoint_page(client: TestClient):
    first = client.get("/maatregelen/valid?limit=2&offset=0&sort_column=Object_ID&sort_order=ASC").json()
    second = client.get("/maatregelen/valid?limit=2&offset=2&sort_column=Object_ID&sort_order=ASC").json()

    assert second["offset"] == 2
    first_codes = {r["Code"] for r in first["results"]}
    second_codes = {r["Code"] for r in second["results"]}
    assert first_codes.isdisjoint(second_codes)


def test_default_sort_is_title_ascending(client: TestClient):
    titles = [r["Title"] for r in client.get("/maatregelen/valid").json()["results"]]

    assert titles == sorted(titles)


@pytest.mark.parametrize(
    "sort_order, reverse",
    [
        pytest.param("ASC", False, id="asc"),
        pytest.param("DESC", True, id="desc"),
    ],
)
def test_sort_by_object_id(client: TestClient, sort_order: str, reverse: bool):
    body = client.get(f"/maatregelen/valid?sort_column=Object_ID&sort_order={sort_order}").json()
    ids = [r["Object_ID"] for r in body["results"]]

    assert ids == sorted(ids, reverse=reverse)


def test_result_matches_the_response_model_shape(client: TestClient, ctx: Context):
    expected: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid")).spec
    model: Type[BaseModel] = ctx.m.get_pydantic_model("beleidsdoel_basic")

    row: Dict[str, dict] = {r["Code"]: r for r in client.get("/beleidsdoelen/valid").json()["results"]}[expected.Code]

    assert set(row.keys()) == set(model.model_fields)
    # No later valid version exists for this lineage, so the enrichment yields None.
    assert row["Next_Version"] is None
