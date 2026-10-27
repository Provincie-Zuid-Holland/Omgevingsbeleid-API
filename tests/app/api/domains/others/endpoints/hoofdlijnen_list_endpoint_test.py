import httpx2

from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec


async def test_lists_the_hoofdlijnen_newest_first(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/hoofdlijnen")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-2", "hoofdlijn-1"]
    )


async def test_lists_the_hoofdlijnen_sort_by_name(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/hoofdlijnen?sort_column=name&sort_order=ASC")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-1", "hoofdlijn-3", "hoofdlijn-2"]
    )


async def test_lists_the_hoofdlijnen_sort_by_kind(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/hoofdlijnen?sort_column=kind&sort_order=ASC")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-2", "hoofdlijn-1"]
    )
