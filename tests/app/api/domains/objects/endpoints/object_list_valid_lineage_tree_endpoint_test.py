from typing import Type

from pydantic import BaseModel
import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BaseObjectSpec, BeleidsdoelSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, object_type, lineage_id, latest_ref, expected_total",
    [
        pytest.param(
            "/beleidsdoelen",
            "beleidsdoel",
            1,
            Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"),
            3,
            id="beleidsdoel-1",
        ),
        pytest.param(
            "/beleidsdoelen",
            "beleidsdoel",
            3,
            Ref(BeleidsdoelSpec, "beleidsdoel_3_latest_valid"),
            4,
            id="beleidsdoel-3-incl-future",
        ),
        pytest.param(
            "/maatregelen", "maatregel", 6, Ref(MaatregelSpec, "maatregel_6_past_end_validity"), 3, id="maatregel-6"
        ),
    ],
)
def test_returns_full_version_history_of_a_lineage(
    client: TestClient,
    ctx: Context,
    prefix: str,
    object_type: str,
    lineage_id: int,
    latest_ref: Ref,
    expected_total: int,
):
    latest: BaseObjectSpec = ctx.f.find(latest_ref).spec

    body = client.get(f"{prefix}/valid/{lineage_id}").json()

    assert body["total"] == expected_total
    assert len(body["results"]) == expected_total
    assert all(r["Code"] == f"{object_type}-{lineage_id}" for r in body["results"])
    assert str(latest.UUID) in {r["UUID"] for r in body["results"]}


def test_tree_includes_future_version_that_valid_list_excludes(client: TestClient, ctx: Context):
    future: BeleidsdoelSpec = ctx.f.find(Ref(BeleidsdoelSpec, "beleidsdoel_3_future")).spec

    tree = {r["UUID"] for r in client.get("/beleidsdoelen/valid/3").json()["results"]}
    valid = {r["UUID"] for r in client.get("/beleidsdoelen/valid").json()["results"]}

    assert str(future.UUID) in tree
    assert str(future.UUID) not in valid


def test_tree_includes_past_end_validity_version_that_valid_list_excludes(client: TestClient, ctx: Context):
    expired: MaatregelSpec = ctx.f.find(Ref(MaatregelSpec, "maatregel_6_past_end_validity")).spec

    tree = {r["UUID"] for r in client.get("/maatregelen/valid/6").json()["results"]}
    valid_codes = {r["Code"] for r in client.get("/maatregelen/valid").json()["results"]}

    assert str(expired.UUID) in tree
    assert expired.Code not in valid_codes


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/beleidsdoelen/valid/999", id="unknown-lineage"),
        pytest.param("/beleidsdoelen/valid/6", id="lineage-id-of-another-type"),
    ],
)
def test_lineage_without_versions_returns_empty(client: TestClient, url: str):
    body = client.get(url).json()

    assert body["total"] == 0
    assert body["results"] == []


def test_default_sort_is_modified_date_descending(client: TestClient):
    mods = [r["Modified_Date"] for r in client.get("/beleidsdoelen/valid/1").json()["results"]]

    assert mods == sorted(mods, reverse=True)


@pytest.mark.parametrize(
    "sort_order, reverse",
    [
        pytest.param("ASC", False, id="asc"),
        pytest.param("DESC", True, id="desc"),
    ],
)
def test_sort_by_modified_date(client: TestClient, sort_order: str, reverse: bool):
    url = f"/beleidsdoelen/valid/1?sort_column=Modified_Date&sort_order={sort_order}"
    mods = [r["Modified_Date"] for r in client.get(url).json()["results"]]

    assert mods == sorted(mods, reverse=reverse)


def test_pagination_caps_page_size_without_changing_total(client: TestClient):
    total = client.get("/beleidsdoelen/valid/3").json()["total"]

    page = client.get("/beleidsdoelen/valid/3?limit=2&offset=0").json()

    assert page["total"] == total
    assert page["limit"] == 2
    assert len(page["results"]) == 2


def test_result_matches_the_response_model_shape(client: TestClient, ctx: Context):
    model: Type[BaseModel] = ctx.m.get_pydantic_model("beleidsdoel_basic")

    row: dict = client.get("/beleidsdoelen/valid/1").json()["results"][0]

    assert set(row.keys()) == set(model.model_fields)
