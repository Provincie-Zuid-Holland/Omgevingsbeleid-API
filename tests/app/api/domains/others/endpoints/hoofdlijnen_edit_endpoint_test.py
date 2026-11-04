import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.others import HoofdlijnTable
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


def _payload(**overrides) -> dict:
    payload = {
        "name": "Edited hoofdlijn name",
        "kind": "Edited hoofdlijn kind",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
async def test_edit_a_hoofdlijn_and_changes_are_persisted_in_db(
    request: pytest.FixtureRequest, session: AsyncSession, ctx: Context, client_fixture: str
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, "hoofdlijn-2")).spec
    payload: dict[str, str] = _payload()
    response = await client.post(
        f"/hoofdlijnen/{original.id}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    # The hoofdlijn changes are persisted
    row: HoofdlijnTable | None = await session.get(HoofdlijnTable, original.id)
    assert row is not None
    assert row.name == payload.get("name")
    assert row.kind == payload.get("kind")


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
async def test_edit_a_hoofdlijn_no_updates_exception(request: pytest.FixtureRequest, ctx: Context, client_fixture: str):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, "hoofdlijn-2")).spec
    response = await client.post(
        f"/hoofdlijnen/{original.id}",
        json={},
    )

    assert response.status_code == 400, response.text
    assert response.json().get("detail") == "Nothing to update"


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
async def test_raises_404_when_hoofdlijn_does_not_exist(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str
):
    client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)
    unknown_uuid = "00000000-0000-0000-0000-000000000000"

    response = await client.post(f"/hoofdlijnen/{unknown_uuid}")

    assert response.status_code == 404, response.text
