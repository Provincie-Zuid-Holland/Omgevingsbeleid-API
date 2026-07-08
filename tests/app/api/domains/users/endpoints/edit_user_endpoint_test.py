import uuid
from typing import Optional

from fastapi.testclient import TestClient
import pytest
from pytest import FixtureRequest
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.tables.others import ChangeLogTable
from app.core.tables.users import IS_ACTIVE, UsersTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


# allowed_roles for the edit_user resolver
ALLOWED_ROL = "Behandelend Ambtenaar"

# A uuid that is guaranteed not to match any seeded user.
NONEXISTENT_UUID = uuid.UUID("00000000-0000-0000-0000-00000000dead")


@pytest.fixture()
def target_uuid(ctx: Context) -> uuid.UUID:
    return ctx.f.primary_key_uuid(Ref(UserSpec, "viewer"))


def test_edit_user_success(admin: TestClient, target_uuid: uuid.UUID, session: Session):
    payload = {
        "Gebruikersnaam": "Edited Name",
        "Email": "edited@pzh.nl",
        "Rol": ALLOWED_ROL,
    }

    response = admin.post(f"/users/{target_uuid}", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    row: Optional[UsersTable] = session.get(UsersTable, target_uuid)
    assert row is not None
    assert row.Gebruikersnaam == "Edited Name"
    assert row.Email == "edited@pzh.nl"
    assert row.Rol == ALLOWED_ROL
    assert row.Status == IS_ACTIVE


def test_edit_user_deactivate_and_reactivate(admin: TestClient, target_uuid: uuid.UUID, session: Session):
    deactivate = admin.post(f"/users/{target_uuid}", json={"IsActive": False})
    assert deactivate.status_code == 200, deactivate.text
    row: Optional[UsersTable] = session.get(UsersTable, target_uuid)
    assert row is not None
    assert row.Status == ""
    assert row.IsActive is False

    reactivate = admin.post(f"/users/{target_uuid}", json={"IsActive": True})
    assert reactivate.status_code == 200, reactivate.text
    session.refresh(row)
    assert row.Status == IS_ACTIVE
    assert row.IsActive is True


def test_edit_user_writes_changelog_without_password(admin: TestClient, target_uuid: uuid.UUID, ctx: Context):
    response = admin.post(f"/users/{target_uuid}", json={"Gebruikersnaam": "Edited Name"})
    assert response.status_code == 200, response.text

    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    change_log: Optional[ChangeLogTable] = ctx.session.scalar(
        select(ChangeLogTable)
        .where(ChangeLogTable.Action_Type == "edit_user")
        .order_by(desc(ChangeLogTable.Created_Date))
    )
    assert change_log is not None
    assert change_log.Created_By_UUID == admin_uuid

    assert '"Gebruikersnaam": "Viewer"' in (change_log.Before or "")
    assert '"Gebruikersnaam": "Edited Name"' in (change_log.After or "")
    assert "Wachtwoord" not in (change_log.Before or "")
    assert "Wachtwoord" not in (change_log.After or "")


def test_edit_user_email_already_in_use(admin: TestClient, target_uuid: uuid.UUID, session: Session, ctx: Context):
    # Try to steal the admin's email.
    response = admin.post(f"/users/{target_uuid}", json={"Email": "admin@pzh.nl"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already in use"

    # The target kept its own email.
    row: Optional[UsersTable] = session.get(UsersTable, target_uuid)
    assert row is not None
    assert row.Email == "viewer@pzh.nl"


def test_edit_user_same_email_is_allowed(admin: TestClient, target_uuid: uuid.UUID):
    # Re-submitting the user's own email must not trip the "already in use" guard.
    response = admin.post(
        f"/users/{target_uuid}",
        json={"Email": "viewer@pzh.nl", "Gebruikersnaam": "Renamed"},
    )
    assert response.status_code == 200, response.text


@pytest.mark.parametrize(
    "client_fixture, use_existing_user, payload, expected_status, expected_detail",
    [
        # Cant be done without an account.
        pytest.param("client", True, {"Gebruikersnaam": "X"}, 401, "Not authenticated", id="unauthenticated"),
        # Ambtenaar lacks `user_can_edit_user`.
        pytest.param("ambtenaar", True, {"Gebruikersnaam": "X"}, 401, "Invalid user role", id="no_permission"),
        # An empty body has nothing to change.
        pytest.param("admin", True, {}, 400, "Nothing to update", id="nothing_to_update"),
        # Editing a user that does not exist.
        pytest.param("admin", False, {"Gebruikersnaam": "X"}, 400, "User does not exist", id="user_does_not_exist"),
        # The resulting email must be valid (EditUser has no field validator, so this is a 400, not 422).
        pytest.param("admin", True, {"Email": "not-an-email"}, 400, "Invalid email", id="invalid_email"),
        # "Superuser" is not in the resolver's allowed_roles.
        pytest.param("admin", True, {"Rol": "Superuser"}, 400, "Invalid Rol", id="disallowed_rol"),
    ],
)
def test_edit_user_rejected(
    request: FixtureRequest,
    target_uuid: uuid.UUID,
    client_fixture: str,
    use_existing_user: bool,
    payload: dict,
    expected_status: int,
    expected_detail: str,
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    target: uuid.UUID = target_uuid if use_existing_user else NONEXISTENT_UUID

    response = test_client.post(f"/users/{target}", json=payload)
    assert response.status_code == expected_status, response.text
    assert response.json()["detail"] == expected_detail
