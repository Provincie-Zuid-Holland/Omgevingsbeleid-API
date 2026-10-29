import uuid

import httpx2
import pytest
from pytest import FixtureRequest
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.domains.users.services.security import Security
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable
from tests.conftest import Context
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref

# allowed_roles for the create_user resolver in tests/_config/main.yml
ALLOWED_ROL = "Regisseur Omgevingsbeleid"


def _payload(**overrides) -> dict:
    payload = {
        "name": "Newbie",
        "email": "newbie@pzh.nl",
        "roles": [ALLOWED_ROL],
    }
    payload.update(overrides)
    return payload


async def test_create_user_success(admin: httpx2.AsyncClient, session: AsyncSession, security: Security):
    response = await admin.post("/users", json=_payload())
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["email"] == "newbie@pzh.nl"
    assert body["roles"] == [ALLOWED_ROL]
    assert body["password"].startswith("change-me-")
    created_id = uuid.UUID(body["id"])

    # The user is persisted and active.
    row: UsersTable | None = await session.get(UsersTable, created_id, options=[selectinload(UsersTable.user_roles)])
    assert row is not None
    assert row.email == "newbie@pzh.nl"
    assert row.roles == [ALLOWED_ROL]
    assert row.is_active

    # The stored password is a hash of the returned plaintext, not the plaintext.
    assert row.password_hashed != body["password"]
    assert (await security.verify_password(body["password"], row.password_hashed)) is True


async def test_create_user_writes_changelog_without_password(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.post("/users", json=_payload(name="Logged", email="logged@pzh.nl"))
    assert response.status_code == 200, response.text

    admin_id: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))
    change_log: ChangeLogTable | None = await ctx.session.scalar(
        select(ChangeLogTable)
        .where(ChangeLogTable.action_type == "create_user")
        .order_by(desc(ChangeLogTable.created_date))
    )
    assert change_log is not None
    assert change_log.created_by_id == admin_id
    assert "password" not in (change_log.after or "")
    assert "password_hashed" not in (change_log.after or "")


async def test_create_user_duplicate_email(admin: httpx2.AsyncClient, session: AsyncSession):
    first = await admin.post("/users", json=_payload(name="Original", email="dup@pzh.nl"))
    assert first.status_code == 200, first.text

    second = await admin.post("/users", json=_payload(name="Duplicate", email="dup@pzh.nl"))
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already in use"

    # Only the first user exists.
    rows = (await session.scalars(select(UsersTable).where(UsersTable.email == "dup@pzh.nl"))).all()
    assert len(rows) == 1


@pytest.mark.parametrize(
    "client_fixture, payload, expected_status, expected_detail",
    [
        # Cant be done without an account
        pytest.param("client", _payload(email="anon@pzh.nl"), 401, "Not authenticated", id="unauthenticated"),
        # Ambtenaar lacks `user_can_create_user`.
        pytest.param("ambtenaar", _payload(email="forbidden@pzh.nl"), 401, "Invalid user role", id="no_permission"),
        # "Superuser" is not in the resolver's allowed_roles.
        pytest.param(
            "admin", _payload(email="wrongrole@pzh.nl", roles=["Superuser"]), 400, "Invalid Roles", id="disallowed_role"
        ),
        # Roles must not be empty.
        pytest.param(
            "admin", _payload(email="noroles@pzh.nl", roles=[]), 400, "At least one role is required", id="no_roles"
        ),
        # Body validation
        pytest.param("admin", _payload(email="not-an-email"), 422, None, id="invalid_email"),
        pytest.param("admin", _payload(name="ab", email="short@pzh.nl"), 422, None, id="short_username"),
    ],
)
async def test_create_user_rejected(
    request: FixtureRequest,
    client_fixture: str,
    payload: dict,
    expected_status: int,
    expected_detail: str,
    session: AsyncSession,
):
    test_client: httpx2.AsyncClient = request.getfixturevalue(client_fixture)

    response = await test_client.post("/users", json=payload)
    assert response.status_code == expected_status, response.text

    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail

    # A rejected request must not persist a user.
    assert await session.scalar(select(UsersTable).where(UsersTable.email == payload["email"])) is None
