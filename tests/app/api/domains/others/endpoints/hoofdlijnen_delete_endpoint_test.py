import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.others import HoofdlijnTable
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
@pytest.mark.parametrize("hoofdlijn_key", ["hoofdlijn-1", "hoofdlijn-2"])
async def test_deletes_the_specified_hoofdlijn(
    request: pytest.FixtureRequest, session: AsyncSession, ctx: Context, client_fixture: str, hoofdlijn_key: str
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, hoofdlijn_key)).spec

    response = await client.delete(f"/hoofdlijnen/{original.id}")

    assert response.status_code == 200, response.text

    # The hoofdlijn is deleted
    row: HoofdlijnTable | None = await session.get(HoofdlijnTable, original.id)
    assert row is None
