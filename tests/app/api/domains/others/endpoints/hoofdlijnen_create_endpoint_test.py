import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tables.others import HoofdlijnTable


def _payload(**overrides) -> dict:
    payload = {
        "name": "New hoofdlijn name",
        "type": "Some hoofdlijn type",
    }
    payload.update(overrides)
    return payload


def test_creates_a_hoofdlijn_and_it_is_persisted_in_db(admin: TestClient, session: Session):
    payload: dict[str, str] = _payload()
    response = admin.post(
        "/hoofdlijnen",
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    created_uuid = uuid.UUID(body["id"])

    # The hoofdlijn is persisted
    row: HoofdlijnTable | None = session.get(HoofdlijnTable, created_uuid)
    assert row is not None
    assert row.name == payload.get("name")
    assert row.type == payload.get("type")
