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


async def test_edits_the_publication_act(admin: httpx2.AsyncClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    title: str = "Edited title"
    subjects: list[str] = ["bodem", "water"]
    response = await admin.post(
        f"/publication-acts/{act_visie.spec.id}", json={"title": title, "meta_data": {"subjects": subjects}}
    )

    assert response.status_code == 200, response.text

    act_edited = await _act(ctx.session, act_visie.spec.id)
    assert act_edited
    assert act_edited.title == title
    assert act_edited.meta_data["subjects"] == subjects


async def test_edits_the_publication_act_no_updates(admin: httpx2.AsyncClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = await admin.post(f"/publication-acts/{act_visie.spec.id}", json={})

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Nothing to update"
