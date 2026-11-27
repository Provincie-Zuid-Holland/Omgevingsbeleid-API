import httpx2
import pytest

from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
@pytest.mark.parametrize("hoofdlijn_key", ["hoofdlijn-1", "hoofdlijn-2"])
async def test_returns_the_requested_hoofdlijn(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, hoofdlijn_key: str
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    expected: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, hoofdlijn_key)).spec

    response = await client.get(f"/hoofdlijnen/{expected.id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(expected.id)
    assert body["name"] == expected.name
    assert body["kind"] == expected.kind


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
async def test_raises_404_when_hoofdlijn_does_not_exist(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/hoofdlijnen/{unknown_id}")

    assert response.status_code == 404, response.text
