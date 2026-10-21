import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.tables.modules import ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectsTable
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


def _get_module(session: Session, module_id: int) -> ModuleTable:
    module = session.scalar(select(ModuleTable).where(ModuleTable.module_id == module_id))
    assert module
    return module


def _get_module_objects(session: Session, module_id: int) -> list[ModuleObjectsTable]:
    module_objects_db: list[ModuleObjectsTable] = list(
        session.scalars(select(ModuleObjectsTable).where(ModuleObjectsTable.module_id == module_id))
    )
    for obj in module_objects_db:
        assert obj
    return module_objects_db


def _get_objects(session: Session, module_object_ids: list[uuid.UUID]) -> list[ObjectsTable]:
    objects_db: list[ObjectsTable] = list(
        session.scalars(select(ObjectsTable).where(ObjectsTable.adjust_on.in_(module_object_ids)))
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
def test_completes_the_module(admin: TestClient, ctx: Context, module_id: int, start_validity: datetime | None):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    payload: dict = {}
    if start_validity:
        payload["start_validity"] = start_validity.isoformat()
    response = admin.post(f"/modules/{module_id}/complete", json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    latest_status: ModuleStatusHistoryTable = _latest_status(ctx.session, module_id)
    assert latest_status.status == "Module afgerond"
    assert latest_status.created_by_id == admin_uuid

    module: ModuleTable = _get_module(ctx.session, module_id)
    assert module.closed is True
    assert module.successful is True
    assert module.modified_by_id == admin_uuid

    module_objects_db: list[ModuleObjectsTable] = _get_module_objects(ctx.session, module_id)
    module_object_ids: set[uuid.UUID] = {obj.id for obj in module_objects_db}
    objects_db: list[ObjectsTable] = _get_objects(ctx.session, module_object_ids)
    assert {obj.title for obj in objects_db} == {obj.title for obj in module_objects_db}
    assert {obj.adjust_on for obj in objects_db} == {obj.id for obj in module_objects_db}
    expected_start_validity: datetime = start_validity if start_validity else datetime(2026, 1, 1, tzinfo=UTC)
    assert {obj.start_validity.replace(tzinfo=UTC) for obj in objects_db} == {expected_start_validity}


def test_completes_the_module_fails_because_module_is_not_vastgesteld(admin: TestClient, ctx: Context):
    module_id: int = 7
    response = admin.post(f"/modules/{module_id}/complete", json={})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Alleen modules met status Vastgesteld kunnen worden afgesloten"
