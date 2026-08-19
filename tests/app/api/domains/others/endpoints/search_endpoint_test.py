from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec
from tests.fixtures.internal.types import Ref


class Result(BaseModel):
    Module_ID: int | None
    Object_Type: str
    Title: str
    Description: str
    Model: dict[str, Any]


class Response(BaseModel):
    total: int
    offset: int
    limit: int
    results: list[Result]


@pytest.mark.parametrize(
    "client_fixture, request_body, expected_refs, total",
    [
        # beleidsdoel 1 for client and admin
        pytest.param(
            "client",
            {
                "query": "%beleidsdoel 1%",
            },
            [
                Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"),
                Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_second_entry"),
            ],
            2,
            id="client-can-view-public-versions-b1",
        ),
        pytest.param(
            "admin",
            {
                "query": "%beleidsdoel 1%",
            },
            [
                Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"),
                Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_third_entry"),
            ],
            2,
            id="admin-can-view-newer-versions-b1",
        ),
        # beleidsdoel 2 which does not have a public module version
        pytest.param(
            "client",
            {
                "query": "%beleidsdoel 2%",
            },
            [
                Ref(BeleidsdoelSpec, "beleidsdoel_2_latest_valid"),
            ],
            1,
            id="client-can-view-public-versions-b2",
        ),
        pytest.param(
            "admin",
            {
                "query": "%beleidsdoel 2%",
            },
            [
                Ref(BeleidsdoelSpec, "beleidsdoel_2_latest_valid"),
                Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_2_first_entry"),
            ],
            2,
            id="admin-can-view-newer-versions-b2",
        ),
        # Searching for beleidsdoel while not having it in the search type wont find results
        pytest.param(
            "admin",
            {"query": "%beleidsdoel 1%", "object_types": ["maatregel"]},
            [],
            0,
            id="dont-search-for-the-type-we-are-searching-for",
        ),
        # Search only for active
        pytest.param(
            "client",
            {
                "query": "%beleidsdoel 1%",
                "include_valids": True,
                "include_modules": False,
            },
            [
                Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"),
            ],
            1,
            id="filter-active",
        ),
        # Search only for modules
        pytest.param(
            "client",
            {
                "query": "%beleidsdoel 1%",
                "include_valids": False,
                "include_modules": True,
            },
            [
                Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_second_entry"),
            ],
            1,
            id="filter-module",
        ),
        # Module ID filters
        pytest.param(
            "admin",
            {
                "query": "%beleidsdoel 1%",
                "include_valids": False,
                "include_modules": True,
                "module_id": 1,
            },
            [
                Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_1_third_entry"),
            ],
            1,
            id="filter-module-with-result",
        ),
        pytest.param(
            "admin",
            {
                "query": "%beleidsdoel 1%",
                "include_valids": False,
                "include_modules": True,
                "module_id": 2,
            },
            [],
            0,
            id="filter-module-without-result",
        ),
    ],
)
def test_search(
    request: FixtureRequest,
    ctx: Context,
    client_fixture: str,
    request_body: dict[str, Any],
    expected_refs: list[Ref],
    total: int | None,
):
    client: TestClient = request.getfixturevalue(client_fixture)
    body = client.post(
        "/search",
        json=request_body,
    ).raise_for_status()
    response = Response.model_validate_json(body.text)

    if total is not None:
        assert response.total == total

    result_uuids: set[UUID] = {UUID(result.Model["UUID"]) for result in response.results}
    expected_uuids: set[UUID] = set(ctx.f.find_uuids(expected_refs))

    assert expected_uuids == result_uuids


@pytest.mark.parametrize(
    "query_params, request_body, expected_status, expected_message, expected_limit",
    [
        pytest.param({}, {}, 422, None, None, id="missing-query"),
        pytest.param({}, {"query": ""}, 422, None, None, id="empty-query"),
        pytest.param(
            {},
            {
                "query": "%beleidsdoel 1%",
                "include_valids": False,
                "include_modules": False,
            },
            422,
            "You must include something",
            None,
            id="nothing-included",
        ),
        pytest.param(
            {"limit": 51},
            {"query": "%beleidsdoel 1%"},
            422,
            "Pagination limit is too high",
            None,
            id="limit-above-maximum",
        ),
        pytest.param(
            {},
            {"query": "%beleidsdoel 1%", "object_types": ["bogus"]},
            422,
            "Allowed Object_Types are",
            None,
            id="unknown-object-type",
        ),
        pytest.param(
            {"limit": 50},
            {"query": "%beleidsdoel 1%"},
            200,
            None,
            50,
            id="limit-at-maximum",
        ),
        pytest.param(
            {"limit": 1001},
            {"query": "%beleidsdoel 1%"},
            200,
            None,
            20,
            id="limit-reset-to-default",
        ),
        pytest.param(
            {},
            {
                "query": "%beleidsdoel 1%",
                "module_id": 1,
                "include_valids": False,
                "include_modules": False,
            },
            200,
            None,
            None,
            id="module-id-forces-include-modules",
        ),
    ],
)
def test_search_request_validation(
    client: TestClient,
    query_params: dict[str, Any],
    request_body: dict[str, Any],
    expected_status: int,
    expected_message: str | None,
    expected_limit: int | None,
):
    response = client.post(
        "/search",
        params=query_params,
        json=request_body,
    )

    assert response.status_code == expected_status, response.text

    if expected_message is not None:
        assert expected_message in response.text

    if expected_limit is not None:
        assert response.json()["limit"] == expected_limit
