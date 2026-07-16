from typing import List

import pytest
from fastapi.testclient import TestClient

from app.api.domains.others.types import StorageFileBasic
from tests.conftest import Context
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.types import Ref


def _uuids(ctx: Context, keys: List[str]) -> List[str]:
    return [str(ctx.f.primary_key_uuid(Ref(StorageFileSpec, key))) for key in keys]


def test_lists_all_storage_files(admin: TestClient, ctx: Context):
    body = admin.get("/storage-files").json()

    assert body["total"] == 3
    assert {r["UUID"] for r in body["results"]} == set(_uuids(ctx, ["file_1", "file_2", "file_3"]))


def test_results_match_the_storage_file_model_shape(admin: TestClient):
    results = admin.get("/storage-files").json()["results"]

    assert results
    for result in results:
        assert set(result.keys()) == set(StorageFileBasic.model_fields)


def test_default_sort_is_created_date_descending(admin: TestClient, ctx: Context):
    # The endpoint forces Created_Date DESC; fixtures are dated 2025-01-01/02/03.
    results = admin.get("/storage-files").json()["results"]

    assert [r["UUID"] for r in results] == _uuids(ctx, ["file_3", "file_2", "file_1"])


def test_pagination_limits_results_but_keeps_total(admin: TestClient, ctx: Context):
    body = admin.get("/storage-files?offset=0&limit=2").json()

    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [r["UUID"] for r in body["results"]] == _uuids(ctx, ["file_3", "file_2"])


def test_pagination_offset_returns_the_next_page(admin: TestClient, ctx: Context):
    body = admin.get("/storage-files?offset=2&limit=2").json()

    assert [r["UUID"] for r in body["results"]] == [str(ctx.f.primary_key_uuid(Ref(StorageFileSpec, "file_1")))]


@pytest.mark.parametrize(
    "client_fixture, owned_keys",
    [
        ("admin", ["file_1", "file_3"]),
        ("ambtenaar", ["file_2"]),
    ],
)
def test_only_mine_filters_on_the_current_user(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, owned_keys: List[str]
):
    client: TestClient = request.getfixturevalue(client_fixture)

    body = client.get("/storage-files?only_mine=true").json()

    assert {r["UUID"] for r in body["results"]} == set(_uuids(ctx, owned_keys))


def test_filter_filename_matches_a_single_file(admin: TestClient, ctx: Context):
    expected: StorageFileSpec = ctx.f.find(Ref(StorageFileSpec, "file_1")).spec

    body = admin.get(f"/storage-files?filter_filename={expected.Filename}").json()

    assert body["total"] == 1
    assert [r["UUID"] for r in body["results"]] == [str(expected.UUID)]


def test_unauthenticated_returns_401(client: TestClient):
    response = client.get("/storage-files")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
