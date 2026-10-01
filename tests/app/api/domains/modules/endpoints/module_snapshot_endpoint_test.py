from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import ModuleStatusCode
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.conftest import Context


def _status_id(session: Session, module_id: int, status: str) -> int:
    status_id = session.scalar(
        select(ModuleStatusHistoryTable.id)
        .where(ModuleStatusHistoryTable.module_id == module_id)
        .where(ModuleStatusHistoryTable.status == status)
    )
    assert status_id
    return status_id


def test_returns_the_objects_as_they_were_at_the_status(admin: TestClient, ctx: Context):
    # The third entry of beleidsdoel-1 and beleidsdoel-2 were added after the Ter Inzage status
    status_id: int = _status_id(ctx.session, 1, ModuleStatusCode.Ter_Inzage)

    response = admin.get(f"/modules/1/snapshot/{status_id}")

    assert response.status_code == 200, response.text
    assert [o["title"] for o in response.json()["objects"]] == [
        "Changed the titel via Module 1",
        "Beleidsdoel 4 from module 1",
    ]
