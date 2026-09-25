import uuid

from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from tests.conftest import Context
from tests.fixtures.internal.spec.asset_spec import AssetSpec
from tests.fixtures.internal.types import Ref

ABSENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def test_get_by_uuid(session: Session, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    repo = AssetRepository()

    found = repo.get_by_id(session, blue_id)
    assert found is not None
    assert found.id == blue_id

    assert repo.get_by_id(session, ABSENT_ID) is None


def test_get_by_uuids(session: Session, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))

    results = AssetRepository().get_by_ids(session, [blue_id, green_id, ABSENT_ID])

    assert {a.id for a in results} == {blue_id, green_id}


def test_get_by_hash_and_content(session: Session, ctx: Context):
    blue = ctx.f.find(Ref(AssetSpec, "blue")).spec
    repo = AssetRepository()

    found = repo.get_by_hash_and_content(session, blue.hash, blue.content)
    assert found is not None
    assert found.id == blue.id

    # Same hash but mismatched content must not match.
    assert repo.get_by_hash_and_content(session, blue.hash, f"{blue.content}-different-content") is None


def test_get_all(session: Session, ctx: Context):
    blue_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "blue"))
    green_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "green"))
    yellow_id = ctx.f.primary_key_uuid(Ref(AssetSpec, "yellow"))

    results = AssetRepository().get_all(session)

    assert {a.id for a in results} == {blue_id, green_id, yellow_id}
