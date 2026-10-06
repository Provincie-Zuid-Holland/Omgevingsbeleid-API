import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.acknowledged_relation_spec import AcknowledgedRelationSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _get_relation(ctx: Context, other: AcknowledgedRelationSpec) -> AcknowledgedRelationsTable:
    stmt = (
        select(AcknowledgedRelationsTable)
        .filter(AcknowledgedRelationsTable.from_code == other.from_code)
        .filter(AcknowledgedRelationsTable.to_code == other.to_code)
        .execution_options(populate_existing=True)
    )
    return ctx.session.scalars(stmt).one()


def test_edits_acknowledged_relation(admin: TestClient, ctx: Context):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, "beleidskeuze_1_beleidskeuze_2_pending")).spec
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = admin.post(
        "/beleidskeuze/acknowledged-relations/2/edit",
        json={"object_type": "beleidskeuze", "object_id": 1, "acknowledged": True, "explanation": "Agreed"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    expected = _get_relation(ctx, other)
    assert expected.to_acknowledged.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert expected.to_acknowledged_by_uuid == admin_uuid
    assert expected.to_explanation == "Agreed"
    assert expected.is_acknowledged is True
    assert expected.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert expected.modified_by_id == admin_uuid
    assert expected.from_acknowledged.replace(tzinfo=UTC) == other.from_acknowledged
    assert expected.from_explanation == other.from_explanation


def test_edits_acknowledged_relation_not_acknowledged(admin: TestClient, ctx: Context):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, "beleidskeuze_3_beleidskeuze_4_acknowledged")).spec
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = admin.post(
        "/beleidskeuze/acknowledged-relations/4/edit",
        json={"object_type": "beleidskeuze", "object_id": 3, "acknowledged": False},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    expected = _get_relation(ctx, other)
    assert expected.to_acknowledged is None
    assert expected.to_acknowledged_by_uuid == admin_uuid
    assert expected.is_acknowledged is False
    assert expected.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert expected.modified_by_id == admin_uuid
    assert expected.from_acknowledged.replace(tzinfo=UTC) == other.from_acknowledged
    assert expected.from_explanation == other.from_explanation
    assert expected.from_explanation == other.from_explanation
    assert expected.to_explanation == other.to_explanation


@pytest.mark.parametrize(
    "field, column",
    [
        pytest.param("denied", "denied", id="denied"),
        pytest.param("deleted", "deleted_at", id="deleted"),
    ],
)
def test_edits_acknowledged_relation_more_properties(admin: TestClient, ctx: Context, field: str, column: str):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, "beleidskeuze_1_beleidskeuze_2_pending")).spec

    response = admin.post(
        "/beleidskeuze/acknowledged-relations/2/edit",
        json={"object_type": "beleidskeuze", "object_id": 1, field: True},
    )

    assert response.status_code == 200, response.text
    expected = _get_relation(ctx, other)
    assert getattr(expected, column).replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert expected.to_acknowledged is None


def test_edits_acknowledged_relation_not_found_returns_400(admin: TestClient, ctx: Context):
    response = admin.post(
        "/beleidskeuze/acknowledged-relations/3/edit",
        json={"object_type": "beleidskeuze", "object_id": 2, "acknowledged": True},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Acknowledged relation not found"


def test_edits_acknowledged_relation_multiple_flags_returns_422(admin: TestClient):
    response = admin.post(
        "/beleidskeuze/acknowledged-relations/2/edit",
        json={"object_type": "beleidskeuze", "object_id": 1, "acknowledged": True, "denied": True},
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Only one of denied, acknowledged, and deleted can be set to True"
    )
