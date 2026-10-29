import uuid

import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.modules import ModuleObjectContextTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


async def _object_context(
    session: AsyncSession, module_id: int, object_type: str, lineage_id: int
) -> ModuleObjectContextTable:
    object_context: ModuleObjectContextTable | None = await session.scalar(
        select(ModuleObjectContextTable)
        .where(ModuleObjectContextTable.module_id == module_id)
        .where(ModuleObjectContextTable.object_type == object_type)
        .where(ModuleObjectContextTable.object_id == lineage_id)
        .execution_options(populate_existing=True)
    )
    assert object_context
    return object_context


async def test_edits_the_object_context(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    payload: dict[str, str] = {
        "action": "Terminate",
        "explanation": "New explanation",
        "conclusion": "New conclusion",
    }

    response = await admin.post(
        "/modules/1/object-context/beleidsdoel/1",
        json=payload,
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    object_context = await _object_context(ctx.session, 1, "beleidsdoel", 1)
    assert object_context.action == payload["action"]
    assert object_context.explanation == payload["explanation"]
    assert object_context.conclusion == payload["conclusion"]
    assert object_context.modified_by_id == admin_uuid


async def test_edits_the_object_context_no_changes(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.post(
        "/modules/1/object-context/beleidsdoel/1",
        json={},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Nothing to update"


async def test_edits_the_object_context_object_not_found(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.post(
        "/modules/1/object-context/beleidsdoel/99999",
        json={"explanation": "New explanation"},
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Module object niet gevonden"
