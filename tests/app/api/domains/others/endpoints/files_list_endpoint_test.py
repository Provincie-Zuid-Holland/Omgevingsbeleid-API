import httpx2
import pytest

from app.api.domains.others.types import StorageFileBasic
from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.types import Ref


async def test_lists_all_storage_files(admin: httpx2.AsyncClient, ctx: Context):
    body = (await admin.get("/storage-files")).json()

    assert body["total"] == 3
    assert {r["id"] for r in body["results"]} == set(
        get_uuids_from_spec(ctx, StorageFileSpec, ["file_1", "file_2", "file_3"])
    )


async def test_results_match_the_storage_file_model_shape(admin: httpx2.AsyncClient):
    results = (await admin.get("/storage-files")).json()["results"]

    assert results
    for result in results:
        assert set(result.keys()) == set(StorageFileBasic.model_fields)


async def test_default_sort_is_created_date_descending(admin: httpx2.AsyncClient, ctx: Context):
    # The endpoint forces created_date DESC; fixtures are dated 2025-01-01/02/03.
    results = (await admin.get("/storage-files")).json()["results"]

    assert [r["id"] for r in results] == get_uuids_from_spec(ctx, StorageFileSpec, ["file_3", "file_2", "file_1"])


async def test_pagination_limits_results_but_keeps_total(admin: httpx2.AsyncClient, ctx: Context):
    body = (await admin.get("/storage-files?offset=0&limit=2")).json()

    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [r["id"] for r in body["results"]] == get_uuids_from_spec(ctx, StorageFileSpec, ["file_3", "file_2"])


async def test_pagination_offset_returns_the_next_page(admin: httpx2.AsyncClient, ctx: Context):
    body = (await admin.get("/storage-files?offset=2&limit=2")).json()

    assert [r["id"] for r in body["results"]] == [str(ctx.f.primary_key_uuid(Ref(StorageFileSpec, "file_1")))]


@pytest.mark.parametrize(
    "client_fixture, owned_keys",
    [
        ("admin", ["file_1", "file_3"]),
        ("ambtenaar", ["file_2"]),
    ],
)
async def test_only_mine_filters_on_the_current_user(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, owned_keys: list[str]
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)

    body = (await client.get("/storage-files?only_mine=true")).json()

    assert {r["id"] for r in body["results"]} == set(get_uuids_from_spec(ctx, StorageFileSpec, owned_keys))


async def test_filter_filename_matches_a_single_file(admin: httpx2.AsyncClient, ctx: Context):
    expected: StorageFileSpec = ctx.f.find(Ref(StorageFileSpec, "file_1")).spec

    body = (await admin.get(f"/storage-files?filter_filename={expected.filename}")).json()

    assert body["total"] == 1
    assert [r["id"] for r in body["results"]] == [str(expected.id)]


async def test_unauthenticated_returns_401(client: httpx2.AsyncClient):
    response = await client.get("/storage-files")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
