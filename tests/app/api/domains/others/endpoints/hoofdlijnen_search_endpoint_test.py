from fastapi.testclient import TestClient

from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec


def test_search_hoofdlijn_newest_first(viewer: TestClient, ctx: Context):
    response = viewer.post("/hoofdlijnen/search?query=Provinciaal")

    assert response.status_code == 200
    assert [r["UUID"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-1"]
    )


def test_search_hoofdlijn_sort_by_name(viewer: TestClient, ctx: Context):
    response = viewer.post("/hoofdlijnen/search?query=aal&sort_column=Name&sort_order=ASC")
    assert response.status_code == 200
    assert [r["UUID"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-1", "hoofdlijn-3", "hoofdlijn-2"]
    )


def test_search_hoofdlijn_sort_by_type(viewer: TestClient, ctx: Context):
    response = viewer.post("/hoofdlijnen/search?query=aal&sort_column=Type&sort_order=ASC")
    assert response.status_code == 200
    assert [r["UUID"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx, HoofdlijnSpec, ["hoofdlijn-3", "hoofdlijn-2", "hoofdlijn-1"]
    )
