import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tables.others import HoofdlijnTable
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
@pytest.mark.parametrize("hoofdlijn_key", ["hoofdlijn-1", "hoofdlijn-2"])
def test_deletes_the_specified_hoofdlijn(
    request: pytest.FixtureRequest, session: Session, ctx: Context, client_fixture: str, hoofdlijn_key: str
):
    client: TestClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, hoofdlijn_key)).spec

    response = client.delete(f"/hoofdlijnen/{original.UUID}")

    assert response.status_code == 200, response.text

    # The hoofdlijn is deleted
    row: HoofdlijnTable | None = session.get(HoofdlijnTable, original.UUID)
    assert row is None
