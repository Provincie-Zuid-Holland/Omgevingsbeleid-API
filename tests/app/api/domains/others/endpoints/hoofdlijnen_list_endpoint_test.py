from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


def _uuids(ctx: Context, keys: list[str]) -> list[str]:
    return [str(ctx.f.primary_key_uuid(Ref(HoofdlijnSpec, key))) for key in keys]


def test_lists_the_hoofdlijnen_newest_first(admin: TestClient, ctx: Context):
    response = admin.get("/hoofdlijnen")

    assert response.status_code == 200
    assert [r["UUID"] for r in response.json().get("results")] == _uuids(ctx, ["hoofdlijn-2", "hoofdlijn-1"])
