from typing import Optional

from sqlalchemy.orm import Session

from app.core.tables.users import UsersTable
from tests.conftest import Context
from tests.fixtures.internal.types import Ref, FixtureData
from tests.fixtures.internal.spec.user_spec import UserSpec


def test_glued_dependency(ctx: Context):
    admin_uuid = ctx.fixtures.primary_key(Ref(UserSpec, "admin"))
    row: Optional[UsersTable] = ctx.session.get(UsersTable, admin_uuid)
    assert row is not None
    assert row.Gebruikersnaam == "Admin"


def test_separate_fixtures(session: Session, fixtures: FixtureData):
    ambtenaar_uuid = fixtures.primary_key(Ref(UserSpec, "ambtenaar"))
    assert session.get(UsersTable, ambtenaar_uuid) is not None


def test_reset_part1(session: Session, fixtures: FixtureData):
    admin = session.get(UsersTable, fixtures.primary_key(Ref(UserSpec, "admin")))
    assert admin is not None
    admin.Gebruikersnaam = "MUTATED"
    session.flush()


def test_reset_part2(session: Session, fixtures: FixtureData):
    # proves rollback reset the seed between tests
    admin = session.get(UsersTable, fixtures.primary_key(Ref(UserSpec, "admin")))
    assert admin is not None
    assert admin.Gebruikersnaam == "Admin"


def test_app_sees_seed(admin, fixtures: FixtureData):
    # proves the app override + seed visibility through a real request
    resp = admin.get(f"/users/{fixtures.primary_key(Ref(UserSpec, 'admin'))}")
    assert resp.status_code == 200
