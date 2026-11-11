import uuid
from datetime import UTC, datetime

import httpx2
import pytest
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.modules import ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectsTable
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


async def _get_module(session: AsyncSession, module_id: int) -> ModuleTable:
    module = await session.scalar(select(ModuleTable).where(ModuleTable.module_id == module_id))
    assert module
    return module


async def _get_module_objects(session: AsyncSession, module_id: int) -> list[ModuleObjectsTable]:
    module_objects_db: list[ModuleObjectsTable] = list(
        await session.scalars(select(ModuleObjectsTable).where(ModuleObjectsTable.module_id == module_id))
    )
    for obj in module_objects_db:
        assert obj
    return module_objects_db


async def _get_objects(session: AsyncSession, module_object_ids: list[uuid.UUID]) -> list[ObjectsTable]:
    objects_db: list[ObjectsTable] = list(
        await session.scalars(select(ObjectsTable).where(ObjectsTable.adjust_on.in_(module_object_ids)))
    )
    for obj in objects_db:
        assert obj
    return objects_db


@pytest.mark.parametrize(
    "module_id, start_validity",
    [
        pytest.param(8, None, id="no-start-validity-given"),
        pytest.param(8, datetime(2025, 11, 25, tzinfo=UTC), id="given-start-validity"),
    ],
)
async def test_completes_the_module(
    admin: httpx2.AsyncClient, ctx: Context, module_id: int, start_validity: datetime | None
):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    payload: dict = {}
    if start_validity:
        payload["start_validity"] = start_validity.isoformat()
    response = await admin.post(f"/modules/{module_id}/complete", json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    latest_status: ModuleStatusHistoryTable = await _latest_status(ctx.session, module_id)
    assert latest_status.status == "Module afgerond"
    assert latest_status.created_by_id == admin_uuid

    module: ModuleTable = await _get_module(ctx.session, module_id)
    assert module.closed is True
    assert module.successful is True
    assert module.modified_by_id == admin_uuid

    module_objects_db: list[ModuleObjectsTable] = await _get_module_objects(ctx.session, module_id)
    module_object_ids: set[uuid.UUID] = {obj.id for obj in module_objects_db}
    objects_db: list[ObjectsTable] = await _get_objects(ctx.session, module_object_ids)
    assert {obj.title for obj in objects_db} == {obj.title for obj in module_objects_db}
    assert {obj.adjust_on for obj in objects_db} == {obj.id for obj in module_objects_db}
    expected_start_validity: datetime = start_validity if start_validity else datetime(2026, 1, 1, tzinfo=UTC)
    assert {obj.start_validity.replace(tzinfo=UTC) for obj in objects_db} == {expected_start_validity}


async def test_completes_the_module_fails_because_module_is_not_vastgesteld(admin: httpx2.AsyncClient, ctx: Context):
    module_id: int = 7
    response = await admin.post(f"/modules/{module_id}/complete", json={})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Alleen modules met status Vastgesteld kunnen worden afgesloten"
