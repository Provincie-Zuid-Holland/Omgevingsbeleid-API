import uuid

import httpx2
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.modules.types import ModuleStatusCode
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


async def _latest_status(session: AsyncSession, module_id: int) -> ModuleStatusHistoryTable:
    status = await session.scalar(
        select(ModuleStatusHistoryTable)
        .where(ModuleStatusHistoryTable.module_id == module_id)
        .order_by(desc(ModuleStatusHistoryTable.id))
    )
    assert status
    return status


async def test_patches_module_status(admin: httpx2.AsyncClient, beheerder: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.patch("/modules/7/status", json={"status": ModuleStatusCode.Ontwerp_GS.value})

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    latest_status: ModuleStatusHistoryTable = await _latest_status(ctx.session, 7)
    assert latest_status.status == ModuleStatusCode.Ontwerp_GS
    assert latest_status.created_by_id == admin_uuid

    # Validator should fail, try with beheerder
    response = await beheerder.patch("/modules/7/status", json={"status": ModuleStatusCode.Vastgesteld.value})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Please run the module validator, there seems to be a problem."

    latest_status: ModuleStatusHistoryTable = await _latest_status(ctx.session, 7)
    assert latest_status.status == ModuleStatusCode.Ontwerp_GS
    assert latest_status.created_by_id == admin_uuid  # latest status by admin


async def test_patches_non_active_status_raises_404(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.patch("/modules/2/status", json={"status": ModuleStatusCode.Ontwerp_GS_Concept.value})
    assert response.status_code == 404, response.text
    body = response.json()
    assert body["detail"] == "De module is nog niet actief"
