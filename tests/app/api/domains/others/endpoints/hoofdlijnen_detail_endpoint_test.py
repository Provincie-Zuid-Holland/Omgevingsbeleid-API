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
