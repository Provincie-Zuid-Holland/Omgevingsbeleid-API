import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from tests.conftest import Context
from tests.fixtures.internal.spec.asset_spec import AssetSpec
from tests.fixtures.internal.types import Ref

ABSENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


async def test_get_by_uuid(session: AsyncSession, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    repo = AssetRepository()

    found = await repo.get_by_id(session, blue_id)
    assert found is not None
    assert found.id == blue_id

    assert await repo.get_by_id(session, ABSENT_ID) is None


async def test_get_by_uuids(session: AsyncSession, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))

    results = await AssetRepository().get_by_ids(session, [blue_id, green_id, ABSENT_ID])

    assert {a.id for a in results} == {blue_id, green_id}


async def test_get_by_hash_and_content(session: AsyncSession, ctx: Context):
    blue = ctx.f.find(Ref(AssetSpec, "blue")).spec
    repo = AssetRepository()

    found = await repo.get_by_hash_and_content(session, blue.hash, blue.content)
    assert found is not None
    assert found.id == blue.id

    # Same hash but mismatched content must not match.
    assert await repo.get_by_hash_and_content(session, blue.hash, f"{blue.content}-different-content") is None


async def test_get_all(session: AsyncSession, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))
    yellow_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "yellow"))

    results = await AssetRepository().get_all(session)

    assert {a.id for a in results} == {blue_id, green_id, yellow_id}
