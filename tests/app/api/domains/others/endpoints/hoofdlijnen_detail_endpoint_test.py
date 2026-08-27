import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
@pytest.mark.parametrize("hoofdlijn_key", ["hoofdlijn-1", "hoofdlijn-2"])
def test_returns_the_requested_hoofdlijn(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, hoofdlijn_key: str
):
    client: TestClient = request.getfixturevalue(client_fixture)
    expected: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, hoofdlijn_key)).spec

    response = client.get(f"/hoofdlijnen/{expected.UUID}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["UUID"] == str(expected.UUID)
    assert body["Name"] == expected.Name
    assert body["Type"] == expected.Type


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
def test_raises_404_when_hoofdlijn_does_not_exist(request: pytest.FixtureRequest, ctx: Context, client_fixture: str):
    client: TestClient = request.getfixturevalue(client_fixture)
    unknown_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/hoofdlijnen/{unknown_uuid}")

    assert response.status_code == 404, response.text
