import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tables.others import HoofdlijnTable
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


def _payload(**overrides) -> dict:
    payload = {
        "Name": "Edited hoofdlijn name",
        "Type": "Edited hoofdlijn type",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
def test_edit_a_hoofdlijn_and_changes_are_persisted_in_db(
    request: pytest.FixtureRequest, session: Session, ctx: Context, client_fixture: str
):
    client: TestClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, "hoofdlijn-2")).spec
    payload: dict[str, str] = _payload()
    response = client.post(
        f"/hoofdlijnen/{original.UUID}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    # The hoofdlijn changes are persisted
    row: HoofdlijnTable | None = session.get(HoofdlijnTable, original.UUID)
    assert row is not None
    assert row.Name == payload.get("Name")
    assert row.Type == payload.get("Type")


@pytest.mark.parametrize("client_fixture", ["admin", "beheerder"])
def test_edit_a_hoofdlijn_no_updates_exception(request: pytest.FixtureRequest, ctx: Context, client_fixture: str):
    client: TestClient = request.getfixturevalue(client_fixture)
    original: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, "hoofdlijn-2")).spec
    response = client.post(
        f"/hoofdlijnen/{original.UUID}",
        json={},
    )

    assert response.status_code == 400, response.text
    assert response.json().get("detail") == "Nothing to update"


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
def test_raises_404_when_hoofdlijn_does_not_exist(request: pytest.FixtureRequest, ctx: Context, client_fixture: str):
    client: TestClient = request.getfixturevalue(client_fixture)
    unknown_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.post(f"/hoofdlijnen/{unknown_uuid}")

    assert response.status_code == 404, response.text
