from typing import Optional
import uuid

import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import ModuleStatusCodeInternal
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _status_count(session: Session, module_id: int) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(ModuleStatusHistoryTable)
            .where(ModuleStatusHistoryTable.Module_ID == module_id)
        )
        or 0
    )


def _latest_status(session: Session, module_id: int) -> Optional[ModuleStatusHistoryTable]:
    return session.scalar(
        select(ModuleStatusHistoryTable)
        .where(ModuleStatusHistoryTable.Module_ID == module_id)
        .order_by(desc(ModuleStatusHistoryTable.Created_Date), desc(ModuleStatusHistoryTable.ID))
    )


def test_closes_an_active_module(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = admin.post("/modules/1/close")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    module = ctx.session.get(ModuleTable, 1)
    assert module
    assert module.Closed is True
    assert module.Successful is False
    assert module.Modified_By_UUID == admin_uuid


def test_creates_a_module_status_history_record(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    before = _status_count(ctx.session, 1)

    response = admin.post("/modules/1/close")

    assert response.status_code == 200, response.text
    assert _status_count(ctx.session, 1) == before + 1

    latest = _latest_status(ctx.session, 1)
    assert latest
    assert latest.Status == ModuleStatusCodeInternal.Gesloten
    assert latest.Created_By_UUID == admin_uuid


def test_already_closed_module_returns_404(admin: TestClient, ctx: Context):
    before = _status_count(ctx.session, 3)

    response = admin.post("/modules/3/close")

    assert response.status_code == 404
    assert response.json()["detail"] == "De module is gesloten"
    assert _status_count(ctx.session, 3) == before


def test_unknown_module_returns_404(admin: TestClient):
    response = admin.post("/modules/999999/close")

    assert response.status_code == 404
    assert response.json()["detail"] == "Module niet gevonden"


def test_module_manager_without_role_permission_can_close(ambtenaar: TestClient, ctx: Context):
    # The ambtenaar role lacks module_can_close_module, but is manager of module 4,
    # so the manager whitelist grants access.
    response = ambtenaar.post("/modules/4/close")

    assert response.status_code == 200, response.text

    module = ctx.session.get(ModuleTable, 4)
    assert module
    assert module.Closed is True


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("admin", 200, None, id="user-with-permission"),
    ],
)
def test_permission_matrix(request: FixtureRequest, client_fixture: str, expected_status: int, expected_detail: str):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    # Module 2 is not managed by the ambtenaar, so the whitelist does not apply here.
    response = test_client.post("/modules/2/close")

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
