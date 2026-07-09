import uuid
from typing import Optional

from fastapi.testclient import TestClient
import pytest
from pytest import FixtureRequest
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.domains.users.services.security import Security
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import IS_ACTIVE, UsersTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


# allowed_roles for the create_user resolver in tests/_config/main.yml
ALLOWED_ROL = "Behandelend Ambtenaar"


def _payload(**overrides) -> dict:
    payload = {
        "Gebruikersnaam": "Newbie",
        "Email": "newbie@pzh.nl",
        "Rol": ALLOWED_ROL,
    }
    payload.update(overrides)
    return payload


def test_create_user_success(admin: TestClient, session: Session, security: Security):
    response = admin.post("/users", json=_payload())
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["Email"] == "newbie@pzh.nl"
    assert body["Rol"] == ALLOWED_ROL
    assert body["Password"].startswith("change-me-")
    created_uuid = uuid.UUID(body["UUID"])

    # The user is persisted and active.
    row: Optional[UsersTable] = session.get(UsersTable, created_uuid)
    assert row is not None
    assert row.Email == "newbie@pzh.nl"
    assert row.Rol == ALLOWED_ROL
    assert row.Status == IS_ACTIVE

    # The stored password is a hash of the returned plaintext, not the plaintext.
    assert row.Wachtwoord != body["Password"]
    assert security.verify_password(body["Password"], row.Wachtwoord) is True


def test_create_user_writes_changelog_without_password(admin: TestClient, ctx: Context):
    response = admin.post("/users", json=_payload(Gebruikersnaam="Logged", Email="logged@pzh.nl"))
    assert response.status_code == 200, response.text

    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    change_log: Optional[ChangeLogTable] = ctx.session.scalar(
        select(ChangeLogTable)
        .where(ChangeLogTable.Action_Type == "create_user")
        .order_by(desc(ChangeLogTable.Created_Date))
    )
    assert change_log is not None
    assert change_log.Created_By_UUID == admin_uuid
    assert "Wachtwoord" not in (change_log.After or "")


def test_create_user_duplicate_email(admin: TestClient, session: Session):
    first = admin.post("/users", json=_payload(Gebruikersnaam="Original", Email="dup@pzh.nl"))
    assert first.status_code == 200, first.text

    second = admin.post("/users", json=_payload(Gebruikersnaam="Duplicate", Email="dup@pzh.nl"))
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already in use"

    # Only the first user exists.
    rows = session.scalars(select(UsersTable).where(UsersTable.Email == "dup@pzh.nl")).all()
    assert len(rows) == 1


@pytest.mark.parametrize(
    "client_fixture, payload, expected_status, expected_detail",
    [
        # Cant be done without an account
        pytest.param("client", _payload(Email="anon@pzh.nl"), 401, "Not authenticated", id="unauthenticated"),
        # Ambtenaar lacks `user_can_create_user`.
        pytest.param("ambtenaar", _payload(Email="forbidden@pzh.nl"), 401, "Invalid user role", id="no_permission"),
        # "Superuser" is not in the resolver's allowed_roles.
        pytest.param(
            "admin", _payload(Email="wrongrole@pzh.nl", Rol="Superuser"), 400, "Invalid Rol", id="disallowed_rol"
        ),
        # Body validation
        pytest.param("admin", _payload(Email="not-an-email"), 422, None, id="invalid_email"),
        pytest.param("admin", _payload(Gebruikersnaam="ab", Email="short@pzh.nl"), 422, None, id="short_username"),
    ],
)
def test_create_user_rejected(
    request: FixtureRequest,
    client_fixture: str,
    payload: dict,
    expected_status: int,
    expected_detail: str,
    session: Session,
):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    response = test_client.post("/users", json=payload)
    assert response.status_code == expected_status, response.text

    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail

    # A rejected request must not persist a user.
    assert session.scalar(select(UsersTable).where(UsersTable.Email == payload["Email"])) is None
