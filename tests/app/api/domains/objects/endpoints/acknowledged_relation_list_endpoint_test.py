import uuid

import httpx2

from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


async def test_lists_acknowledged_relations(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.get("/beleidskeuze/acknowledged-relations/1")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    relation = body[0]
    assert relation["created_by_id"] == str(admin_uuid)
    assert relation["modified_by_id"] == str(admin_uuid)
    assert relation["deleted_at"] is None
    assert relation["denied"] is None
    assert relation["requested_by_code"] == "beleidskeuze-1"
    assert relation["version"] == 1
    side_a = relation["side_a"]
    assert side_a["object_id"] == 1
    assert side_a["object_type"] == "beleidskeuze"
    side_b = relation["side_b"]
    assert side_b["object_id"] == 2
    assert side_b["object_type"] == "beleidskeuze"


async def test_lists_acknowledged_relations_acknowledged(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.get("/beleidskeuze/acknowledged-relations/3?acknowledged=true")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    relation = body[0]
    assert relation["created_by_id"] == str(admin_uuid)
    assert relation["modified_by_id"] == str(admin_uuid)
    assert relation["deleted_at"] is None
    assert relation["denied"] is None
    assert relation["requested_by_code"] == "beleidskeuze-3"
    assert relation["version"] == 1
    side_a = relation["side_a"]
    assert side_a["object_id"] == 3
    assert side_a["object_type"] == "beleidskeuze"
    side_b = relation["side_b"]
    assert side_b["object_id"] == 4
    assert side_b["object_type"] == "beleidskeuze"


async def test_lists_acknowledged_relations_not_acknowledged(admin: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await admin.get("/beleidskeuze/acknowledged-relations/1?acknowledged=false")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    relation = body[0]
    assert relation["created_by_id"] == str(admin_uuid)
    assert relation["modified_by_id"] == str(admin_uuid)
    assert relation["deleted_at"] is None
    assert relation["denied"] is None
    assert relation["requested_by_code"] == "beleidskeuze-1"
    assert relation["version"] == 1
    side_a = relation["side_a"]
    assert side_a["object_id"] == 1
    assert side_a["object_type"] == "beleidskeuze"
    side_b = relation["side_b"]
    assert side_b["object_id"] == 2
    assert side_b["object_type"] == "beleidskeuze"


async def test_lists_acknowledged_relations_inactive(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/beleidskeuze/acknowledged-relations/1?show_inactive=true")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 3
    assert {"beleidskeuze-1"} == {r["requested_by_code"] for r in body}
    assert {"beleidskeuze-1"} == {f"{r['side_a']['object_type']}-{r['side_a']['object_id']}" for r in body}
    assert ["beleidskeuze-2", "beleidskeuze-3", "beleidskeuze-4"] == [
        f"{r['side_b']['object_type']}-{r['side_b']['object_id']}" for r in body
    ]


async def test_lists_acknowledged_requested_by(beheerder: httpx2.AsyncClient, ctx: Context):
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    response = await beheerder.get("/beleidskeuze/acknowledged-relations/1?requested_by_us=true")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    relation = body[0]
    assert relation["created_by_id"] == str(admin_uuid)
    assert relation["modified_by_id"] == str(admin_uuid)
    assert relation["deleted_at"] is None
    assert relation["denied"] is None
    assert relation["requested_by_code"] == "beleidskeuze-1"
    assert relation["version"] == 1
    side_a = relation["side_a"]
    assert side_a["object_id"] == 1
    assert side_a["object_type"] == "beleidskeuze"
    side_b = relation["side_b"]
    assert side_b["object_id"] == 2
    assert side_b["object_type"] == "beleidskeuze"
