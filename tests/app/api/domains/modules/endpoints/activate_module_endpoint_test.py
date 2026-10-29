import uuid

import httpx2
import pytest
from pytest import FixtureRequest
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.modules.types import ModuleStatusCode
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


async def _status_count(session: AsyncSession, module_id: int) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(ModuleStatusHistoryTable)
            .where(ModuleStatusHistoryTable.module_id == module_id)
        )
        or 0
    )


async def _latest_status(session: AsyncSession, module_id: int) -> ModuleStatusHistoryTable | None:
    return await session.scalar(
        select(ModuleStatusHistoryTable)
        .where(ModuleStatusHistoryTable.module_id == module_id)
        .order_by(desc(ModuleStatusHistoryTable.created_date), desc(ModuleStatusHistoryTable.id))
    )


async def test_activates_an_inactive_module(admin: httpx2.AsyncClient, ctx: Context):
    admin_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = await admin.post("/modules/2/activate")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    module = await ctx.session.get(ModuleTable, 2)
    assert module
    assert module.activated is True
    assert module.modified_by_id == admin_id


async def test_creates_a_module_status_history_record(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    before = await _status_count(ctx.session, 2)

    response = await admin.post("/modules/2/activate")

    assert response.status_code == 200, response.text
    assert await _status_count(ctx.session, 2) == before + 1

    latest = await _latest_status(ctx.session, 2)
    assert latest
    assert latest.status == ModuleStatusCode.Ontwerp_GS_Concept
    assert latest.created_by_id == admin_uuid


async def test_already_activated_module_returns_400(admin: httpx2.AsyncClient, ctx: Context):
    before = await _status_count(ctx.session, 1)

    response = await admin.post("/modules/1/activate")

    assert response.status_code == 400
    assert response.json()["detail"] == "The module is already activated"
    assert await _status_count(ctx.session, 1) == before


async def test_unknown_module_returns_404(admin: httpx2.AsyncClient):
    response = await admin.post("/modules/999999/activate")

    assert response.status_code == 404
    assert response.json()["detail"] == "Module niet gevonden"


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("admin", 200, None, id="manager-with-permission"),
    ],
)
async def test_permission_matrix(
    request: FixtureRequest, client_fixture: str, expected_status: int, expected_detail: str
):
    test_client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)

    response = await test_client.post("/modules/2/activate")

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
