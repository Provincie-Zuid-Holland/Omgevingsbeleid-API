import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.modules.types import ModuleStatusCode
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.conftest import Context


async def _status_id(session: AsyncSession, module_id: int, status: str) -> int:
    status_id = await session.scalar(
        select(ModuleStatusHistoryTable.id)
        .where(ModuleStatusHistoryTable.module_id == module_id)
        .where(ModuleStatusHistoryTable.status == status)
    )
    assert status_id
    return status_id


async def test_returns_the_objects_as_they_were_at_the_status(admin: httpx2.AsyncClient, ctx: Context):
    # The third entry of beleidsdoel-1 and beleidsdoel-2 were added after the Ter Inzage status
    status_id: int = await _status_id(ctx.session, 1, ModuleStatusCode.Ter_Inzage)

    response = await admin.get(f"/modules/1/snapshot/{status_id}")

    assert response.status_code == 200, response.text
    assert [o["title"] for o in response.json()["objects"]] == [
        "Changed the titel via Module 1",
        "Beleidsdoel 4 from module 1",
    ]


async def test_doesnt_find_module_status(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/modules/1/snapshot/9999")
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Module status niet gevonden"
