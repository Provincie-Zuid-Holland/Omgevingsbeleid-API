import httpx2

from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec


async def test_search_hoofdlijn_newest_first(viewer: httpx2.AsyncClient, ctx: Context):
    response = await viewer.post("/hoofdlijnen/search?query=Provinciaal")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-1"]
    )


async def test_search_hoofdlijn_sort_by_name(viewer: httpx2.AsyncClient, ctx: Context):
    response = await viewer.post("/hoofdlijnen/search?query=aal&sort_column=name&sort_order=ASC")
    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-1", "hoofdlijn-3", "hoofdlijn-2"]
    )


async def test_search_hoofdlijn_sort_by_kind(viewer: httpx2.AsyncClient, ctx: Context):
    response = await viewer.post("/hoofdlijnen/search?query=aal&sort_column=kind&sort_order=ASC")
    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-2", "hoofdlijn-1"]
    )
