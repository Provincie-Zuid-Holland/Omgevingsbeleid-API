import uuid
from datetime import UTC, datetime

import httpx2
import pytest
from sqlalchemy import select

from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.acknowledged_relation_spec import AcknowledgedRelationSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _payload(object_id: int, object_type: str, explanation: str) -> dict:
    return {
        "object_id": object_id,
        "object_type": object_type,
        "explanation": explanation,
    }


async def _get_relations(ctx: Context, from_code: str, to_code: str) -> list[AcknowledgedRelationsTable]:
    stmt = (
        select(AcknowledgedRelationsTable)
        .filter(AcknowledgedRelationsTable.from_code == from_code)
        .filter(AcknowledgedRelationsTable.to_code == to_code)
        .order_by(AcknowledgedRelationsTable.version)
        .execution_options(populate_existing=True)
    )
    return list((await ctx.session.scalars(stmt)).all())


async def _get_relation(ctx: Context, from_code: str, to_code: str) -> AcknowledgedRelationsTable:
    relations: list[AcknowledgedRelationsTable] = await _get_relations(ctx, from_code, to_code)
    assert len(relations) == 1
    return relations[0]


async def test_adds_acknowledged_relations_to_another_object(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.post(
        "/beleidskeuze/acknowledged-relations/1", json=_payload(8, "beleidskeuze", "Testing purpose")
    )

    relation_before: AcknowledgedRelationsTable = await _get_relation(ctx, "beleidskeuze-1", "beleidskeuze-8")
    assert relation_before.from_acknowledged and relation_before.to_acknowledged is None

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    relation_after: AcknowledgedRelationsTable = await _get_relation(ctx, "beleidskeuze-1", "beleidskeuze-8")

    assert relation_after.to_acknowledged is None
    assert relation_after.to_acknowledged_by_uuid is None
    assert relation_after.to_explanation == ""
    assert relation_after.is_acknowledged is False
    assert relation_after.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation_after.modified_by_id == admin_uuid
    assert relation_after.from_acknowledged.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation_after.from_explanation == "Testing purpose"


async def test_stores_the_sides_sorted_by_code(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.post(
        "/beleidskeuze/acknowledged-relations/8", json=_payload(1, "beleidskeuze", "Testing purpose")
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    relation: AcknowledgedRelationsTable = await _get_relation(ctx, "beleidskeuze-1", "beleidskeuze-8")
    assert relation.version == 1
    assert relation.requested_by_code == "beleidskeuze-8"
    assert relation.created_by_id == admin_uuid
    assert relation.created_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation.to_acknowledged.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation.to_acknowledged_by_uuid == admin_uuid
    assert relation.to_explanation == "Testing purpose"
    assert relation.from_acknowledged is None
    assert relation.from_acknowledged_by_uuid is None


async def test_approves_the_existing_request_of_the_other_side(admin: httpx2.AsyncClient, ctx: Context):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, "beleidskeuze_1_beleidskeuze_2_pending")).spec
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response = await admin.post("/beleidskeuze/acknowledged-relations/2", json=_payload(1, "beleidskeuze", "Agreed"))

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Updated existing request"

    relation: AcknowledgedRelationsTable = await _get_relation(ctx, other.from_code, other.to_code)
    assert relation.version == other.version
    assert relation.requested_by_code == other.requested_by_code
    assert relation.is_acknowledged is True
    assert relation.to_acknowledged.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation.to_acknowledged_by_uuid == admin_uuid
    assert relation.to_explanation == "Agreed"
    assert relation.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
    assert relation.modified_by_id == admin_uuid
    assert relation.from_acknowledged.replace(tzinfo=UTC) == other.from_acknowledged
    assert relation.from_explanation == other.from_explanation


@pytest.mark.parametrize(
    "fixture_key, lineage_id, object_id",
    [
        pytest.param("beleidskeuze_1_beleidskeuze_2_pending", 1, 2, id="already-requested-by-me"),
        pytest.param("beleidskeuze_3_beleidskeuze_4_acknowledged", 4, 3, id="already-acknowledged"),
    ],
)
async def test_existing_relation_returns_409_old(
    admin: httpx2.AsyncClient, ctx: Context, fixture_key: str, lineage_id: int, object_id: int
):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, fixture_key)).spec

    response = await admin.post(
        f"/beleidskeuze/acknowledged-relations/{lineage_id}",
        json=_payload(object_id, "beleidskeuze", "Testing purpose"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Existing relation(request), either edit or delete first"
    relation: AcknowledgedRelationsTable = await _get_relation(ctx, other.from_code, other.to_code)
    assert relation.from_explanation == other.from_explanation
    assert relation.to_explanation == other.to_explanation


async def test_existing_relation_returns_409(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.post(
        "/beleidskeuze/acknowledged-relations/1",
        json=_payload(2, "beleidskeuze", "Testing purpose"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Existing relation(request), either edit or delete first"


@pytest.mark.parametrize(
    "fixture_key",
    [
        pytest.param("beleidskeuze_1_beleidskeuze_3_denied", id="denied"),
        pytest.param("beleidskeuze_1_beleidskeuze_4_deleted", id="deleted"),
    ],
)
async def test_inactive_relation_creates_a_new_version(admin: httpx2.AsyncClient, ctx: Context, fixture_key: str):
    other = ctx.f.find(Ref(AcknowledgedRelationSpec, fixture_key)).spec
    _, other_object_id = other.to_code.split("-")

    response = await admin.post(
        "/beleidskeuze/acknowledged-relations/1",
        json=_payload(int(other_object_id), "beleidskeuze", "Second attempt"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    relations: list[AcknowledgedRelationsTable] = await _get_relations(ctx, other.from_code, other.to_code)
    assert [relation.version for relation in relations] == [1, 2]


async def test_invalid_object_type_returns_400(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.post(
        "/beleidskeuze/acknowledged-relations/1", json=_payload(1, "beleidsdoel", "Testing purpose")
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid object_type"
    assert await _get_relations(ctx, "beleidsdoel-1", "beleidskeuze-1") == []
