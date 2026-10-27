import httpx2
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables.objects import ObjectsTable
from tests.conftest import Context


async def _get_object(session: AsyncSession, object_type: str, object_id: int) -> ObjectsTable:
    await session.flush()
    object_result = await session.scalar(
        select(ObjectsTable)
        .filter(ObjectsTable.object_type == object_type)
        .filter(ObjectsTable.object_id == object_id)
        .order_by(desc(ObjectsTable.modified_date))
        .execution_options(populate_existing=True)
    )
    assert object_result
    return object_result


async def test_deletes_atemporal_object(admin: httpx2.AsyncClient, ctx: Context):
    object_before = await _get_object(ctx.session, "verplicht_programma", 1)
    assert object_before.end_validity is None

    response = await admin.delete("/verplicht-programma/1")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    object_after = await _get_object(ctx.session, "verplicht_programma", 1)
    assert object_after.end_validity is not None

    # TODO this will trigger an error, because end_validity from db doesn't have timezone info
    #
    # response = await admin.delete("/verplicht-programma/1")
    #
    # assert response.status_code == 400, response.text
    # assert response.json()["detail"] == "Object is already deleted"


async def test_deletes_atemporal_object_object_not_existing(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.delete("/verplicht-programma/9999")

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Object not found"
