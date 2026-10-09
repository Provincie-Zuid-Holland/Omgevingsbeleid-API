from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.tables.objects import ObjectsTable
from tests.conftest import Context


def _get_object(session: Session, object_type: str, object_id: int) -> ObjectsTable:
    session.flush()
    object_result = session.scalar(
        select(ObjectsTable)
        .filter(ObjectsTable.object_type == object_type)
        .filter(ObjectsTable.object_id == object_id)
        .order_by(desc(ObjectsTable.modified_date))
        .execution_options(populate_existing=True)
    )
    assert object_result
    return object_result


def test_deletes_atemporal_object(admin: TestClient, ctx: Context):
    object_before = _get_object(ctx.session, "verplicht_programma", 1)
    assert object_before.end_validity is None

    response = admin.delete("/verplicht-programma/1")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    object_after = _get_object(ctx.session, "verplicht_programma", 1)
    assert object_after.end_validity is not None

    # TODO this will trigger an error, because end_validity from db doesn't have timezone info
    #
    # response = admin.delete("/verplicht-programma/1")
    #
    # assert response.status_code == 400, response.text
    # assert response.json()["detail"] == "Object is already deleted"


def test_deletes_atemporal_object_object_not_existing(admin: TestClient, ctx: Context):
    response = admin.delete("/verplicht-programma/9999")

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Object not found"
