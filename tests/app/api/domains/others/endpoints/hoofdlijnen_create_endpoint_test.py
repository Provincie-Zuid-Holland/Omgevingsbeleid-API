import uuid

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.others import HoofdlijnTable


def _payload(**overrides) -> dict:
    payload = {
        "name": "New hoofdlijn name",
        "kind": "Some hoofdlijn kind",
    }
    payload.update(overrides)
    return payload


async def test_creates_a_hoofdlijn_and_it_is_persisted_in_db(admin: httpx2.AsyncClient, session: AsyncSession):
    payload: dict[str, str] = _payload()
    response = await admin.post(
        "/hoofdlijnen",
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    created_uuid = uuid.UUID(body["id"])

    # The hoofdlijn is persisted
    row: HoofdlijnTable | None = await session.get(HoofdlijnTable, created_uuid)
    assert row is not None
    assert row.name == payload.get("name")
    assert row.kind == payload.get("kind")
