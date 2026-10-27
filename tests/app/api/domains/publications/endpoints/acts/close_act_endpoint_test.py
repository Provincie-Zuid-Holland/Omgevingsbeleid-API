from datetime import UTC, datetime

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.publications import PublicationActTable
from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
)
from tests.fixtures.internal.types import Ref


async def _act(session: AsyncSession, act_id: int) -> PublicationActTable | None:
    return await session.get(PublicationActTable, act_id)


async def test_closes_the_publication_act(admin: httpx2.AsyncClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = await admin.post(f"/publication-acts/{act_visie.spec.id}/close")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    act_updated = await _act(ctx.session, act_visie.spec.id)
    assert act_updated
    assert act_updated.is_active is False
    assert act_updated.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
