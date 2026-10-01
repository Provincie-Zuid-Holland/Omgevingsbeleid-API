import uuid

from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.tables.modules import ModuleObjectsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _get_latest_module_object(
    session: Session, module_id: int, object_type: str, lineage_id: int
) -> ModuleObjectsTable:
    module_object = session.scalar(
        select(ModuleObjectsTable)
        .where(ModuleObjectsTable.module_id == module_id)
        .where(ModuleObjectsTable.object_type == object_type)
        .where(ModuleObjectsTable.object_id == lineage_id)
        .order_by(desc(ModuleObjectsTable.modified_date))
    )
    assert module_object
    return module_object


def test_removes_module_object(admin: TestClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    previous_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(ModuleBeleidsdoelSpec, "mod_1_beleidsdoel_4_first_entry"))

    module_id = 1
    object_type = "beleidsdoel"
    object_id = 4
    response = admin.delete(f"/modules/{module_id}/remove/{object_type}/{object_id}")

    assert response.status_code == 200, response.text
    new_module_object = _get_latest_module_object(ctx.session, module_id, object_type, object_id)

    assert new_module_object.id != previous_uuid
    assert new_module_object.adjust_on == previous_uuid
    assert new_module_object.deleted is True
    assert new_module_object.title == "Beleidsdoel 4 from module 1"
    assert new_module_object.modified_by_id == admin_uuid
