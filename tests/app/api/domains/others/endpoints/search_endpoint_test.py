from typing import Any, Dict, List, Optional, Set
from uuid import UUID
import pytest

from pydantic import BaseModel
from fastapi.testclient import TestClient

from tests.conftest import Context
from pytest import FixtureRequest
from tests.fixtures.internal.types import Ref
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec
from tests.fixtures.internal.spec.modules import ModuleBeleidsdoelSpec


class Result(BaseModel):
    Module_ID: Optional[int]
    Object_Type: str
    Title: str
    Description: str
    Model: Dict[str, Any]


class Response(BaseModel):
    total: int
    offset: int
    limit: int
    results: List[Result]


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
    request_body: Dict[str, Any],
    expected_refs: List[Ref],
    total: Optional[int],
):
    client: TestClient = request.getfixturevalue(client_fixture)
    body = client.post(
        "/search",
        json=request_body,
    ).raise_for_status()
    response = Response.model_validate_json(body.text)

    if total is not None:
        assert response.total == total

    result_uuids: Set[UUID] = {UUID(result.Model["UUID"]) for result in response.results}
    expected_uuids: Set[UUID] = set(ctx.f.find_uuids(expected_refs))

    assert expected_uuids == result_uuids
