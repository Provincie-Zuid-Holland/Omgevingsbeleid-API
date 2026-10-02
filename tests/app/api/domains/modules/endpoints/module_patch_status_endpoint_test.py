import uuid

from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import ModuleStatusCode
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _latest_status(session: Session, module_id: int) -> ModuleStatusHistoryTable:
    status = session.scalar(
        select(ModuleStatusHistoryTable)
        .where(ModuleStatusHistoryTable.module_id == module_id)
        .order_by(desc(ModuleStatusHistoryTable.id))
    )
    assert status
    return status


def test_patches_module_status(admin: TestClient, beheerder: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = admin.patch("/modules/7/status", json={"status": ModuleStatusCode.Ontwerp_GS.value})

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    latest_status: ModuleStatusHistoryTable = _latest_status(ctx.session, 7)
    assert latest_status.status == ModuleStatusCode.Ontwerp_GS
    assert latest_status.created_by_id == admin_uuid

    # Validator should fail, try with beheerder
    response = beheerder.patch("/modules/7/status", json={"status": ModuleStatusCode.Vastgesteld.value})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Please run the module validator, there seems to be a problem."

    latest_status: ModuleStatusHistoryTable = _latest_status(ctx.session, 7)
    assert latest_status.status == ModuleStatusCode.Ontwerp_GS
    assert latest_status.created_by_id == admin_uuid  # latest status by admin


def test_patches_non_active_status_raises_404(admin: TestClient, ctx: Context):
    response = admin.patch("/modules/2/status", json={"status": ModuleStatusCode.Ontwerp_GS_Concept.value})
    assert response.status_code == 404, response.text
    body = response.json()
    assert body["detail"] == "De module is nog niet actief"
