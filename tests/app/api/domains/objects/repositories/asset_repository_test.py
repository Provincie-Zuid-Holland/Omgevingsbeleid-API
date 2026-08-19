import uuid

from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from tests.conftest import Context
from tests.fixtures.internal.spec.asset_spec import AssetSpec
from tests.fixtures.internal.types import Ref

ABSENT_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def test_get_by_uuid(session: Session, ctx: Context):
    blue_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    repo = AssetRepository()

    found = repo.get_by_uuid(session, blue_uuid)
    assert found is not None
    assert found.UUID == blue_uuid

    assert repo.get_by_uuid(session, ABSENT_UUID) is None


def test_get_by_uuids(session: Session, ctx: Context):
    blue_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))

    results = AssetRepository().get_by_uuids(session, [blue_uuid, green_uuid, ABSENT_UUID])

    assert {a.UUID for a in results} == {blue_uuid, green_uuid}


def test_get_by_hash_and_content(session: Session, ctx: Context):
    blue = ctx.f.find(Ref(AssetSpec, "blue")).spec
    repo = AssetRepository()

    found = repo.get_by_hash_and_content(session, blue.Hash, blue.Content)
    assert found is not None
    assert found.UUID == blue.UUID

    # Same hash but mismatched content must not match.
    assert repo.get_by_hash_and_content(session, blue.Hash, f"{blue.Content}-different-content") is None


def test_get_all(session: Session, ctx: Context):
    blue_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))
    yellow_uuid = ctx.f.primary_key_uuid(Ref(AssetSpec, "yellow"))

    results = AssetRepository().get_all(session)

    assert {a.UUID for a in results} == {blue_uuid, green_uuid, yellow_uuid}
