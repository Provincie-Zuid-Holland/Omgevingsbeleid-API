from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, List, Optional

import pytest
from httpx2 import Response
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleBeleidskeuzeSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _fetch_draft(session: Session, draft_uuid: uuid.UUID) -> ModuleObjectsTable:
    draft: Optional[ModuleObjectsTable] = session.get(ModuleObjectsTable, draft_uuid)
    assert draft
    return draft


def _assert_same_datetime(actual: datetime, expected: Optional[datetime] = None):
    expected = expected or datetime.now(timezone.utc)
    difference: timedelta = abs(actual.replace(tzinfo=None) - expected.replace(tzinfo=None))
    assert difference <= timedelta(milliseconds=1), f"{actual} differs {difference} from {expected}"


def test_patch_adds_a_new_draft_to_the_lineage(admin: TestClient, ctx: Context):
    previous_draft: ModuleBeleidskeuzeSpec = ctx.f.find(
        Ref(ModuleBeleidskeuzeSpec, "mod_5_beleidskeuze_1_first_entry")
    ).spec
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Title": "Patched via module 5"})

    assert response.status_code == 200, response.text
    body: Dict[str, Any] = response.json()
    assert set(body.keys()) == {"Object_ID", "UUID"}
    assert body["Object_ID"] == 1
    assert body["UUID"] != str(previous_draft.UUID)

    new_draft: ModuleObjectsTable = _fetch_draft(ctx.session, uuid.UUID(body["UUID"]))
    assert new_draft.Module_ID == 5
    assert new_draft.Code == previous_draft.Code
    assert new_draft.Adjust_On == previous_draft.UUID
    assert new_draft.Title == "Patched via module 5"
    assert new_draft.Modified_By_UUID == admin_uuid
    _assert_same_datetime(new_draft.Modified_Date)

    all_drafts: List[ModuleObjectsTable] = list(
        ctx.session.scalars(
            select(ModuleObjectsTable)
            .where(ModuleObjectsTable.Module_ID == 5)
            .where(ModuleObjectsTable.Code == previous_draft.Code)
        )
    )
    assert {draft.UUID for draft in all_drafts} == {
        previous_draft.UUID,
        new_draft.UUID,
    }


def test_fields_left_out_are_copied_from_the_previous_draft(admin: TestClient, ctx: Context):
    previous_draft: ModuleBeleidskeuzeSpec = ctx.f.find(
        Ref(ModuleBeleidskeuzeSpec, "mod_5_beleidskeuze_1_first_entry")
    ).spec

    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Title": "Only the title changes"})

    assert response.status_code == 200, response.text
    new_draft: ModuleObjectsTable = _fetch_draft(ctx.session, uuid.UUID(response.json()["UUID"]))
    assert new_draft.Description == previous_draft.Description
    assert new_draft.Explanation == previous_draft.Explanation
    assert new_draft.Hierarchy_Code == previous_draft.Hierarchy_Code
    _assert_same_datetime(new_draft.Start_Validity, previous_draft.Start_Validity)
    _assert_same_datetime(new_draft.Created_Date, previous_draft.Created_Date)
    assert new_draft.Created_By_UUID == previous_draft.Created_By_UUID


def test_patch_accepts_a_list_field(admin: TestClient, ctx: Context):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Themas": ["natuur", "water"]})

    assert response.status_code == 200, response.text
    new_draft: ModuleObjectsTable = _fetch_draft(ctx.session, uuid.UUID(response.json()["UUID"]))
    assert new_draft.Themas == ["natuur", "water"]


@pytest.mark.parametrize(
    "fixture_key, lineage_id, expect_cached_title",
    [
        pytest.param("mod_5_beleidskeuze_1_first_entry", 1, False, id="lineage-with-live-version"),
        pytest.param("mod_5_beleidskeuze_510_first_entry", 510, True, id="lineage-only-in-module"),
    ],
)
def test_title_is_cached_on_the_static_only_without_a_live_version(
    admin: TestClient,
    ctx: Context,
    fixture_key: str,
    lineage_id: int,
    expect_cached_title: bool,
):
    draft: ModuleBeleidskeuzeSpec = ctx.f.find(Ref(ModuleBeleidskeuzeSpec, fixture_key)).spec
    new_title: str = "Title used for the cache check"

    object_static: Optional[ObjectStaticsTable] = ctx.session.get(ObjectStaticsTable, draft.Code)
    assert object_static
    object_static.Cached_Title = "Title before the patch"
    ctx.session.flush()

    response: Response = admin.patch(f"/modules/5/object/beleidskeuze/{lineage_id}", json={"Title": new_title})

    assert response.status_code == 200, response.text
    ctx.session.expire_all()
    assert object_static.Cached_Title == (new_title if expect_cached_title else "Title before the patch")


def test_hierarchy_code_can_be_changed(admin: TestClient, ctx: Context):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Hierarchy_Code": "beleidsdoel-2"})

    assert response.status_code == 200, response.text
    new_draft: ModuleObjectsTable = _fetch_draft(ctx.session, uuid.UUID(response.json()["UUID"]))
    assert new_draft.Hierarchy_Code == "beleidsdoel-2"


@pytest.mark.parametrize(
    "payload, invalid_field",
    [
        pytest.param({"Title": "<b>Bold</b> title"}, "Title", id="html-in-plain-text-field"),
        pytest.param({"Description": "<script>alert(1)</script>"}, "Description", id="forbidden-html-tag"),
        pytest.param({"Hierarchy_Code": "maatregel-1"}, "Hierarchy_Code", id="code-of-a-disallowed-type"),
        pytest.param({"Hierarchy_Code": "beleidsdoel-999"}, "Hierarchy_Code", id="code-that-does-not-exist"),
        pytest.param({"Gebiedengroep_Code": "beleidsdoel-1"}, "Gebiedengroep_Code", id="wrong-type-for-gebiedengroep"),
    ],
)
def test_invalid_body_returns_422(admin: TestClient, payload: Dict[str, Any], invalid_field: str):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json=payload)

    assert response.status_code == 422, response.text
    assert invalid_field in {error["loc"][-1] for error in response.json()["detail"]}


def test_lineage_outside_the_module_returns_404(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/3", json={"Title": "Not in this module"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Module object niet gevonden"


def test_empty_body_returns_400(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Niets om aan te passen"


def test_unknown_lineage_returns_404(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/999", json={"Title": "Does not exist"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Object static niet gevonden"


def test_locked_module_returns_400(admin: TestClient, ctx: Context):
    module: Optional[ModuleTable] = ctx.session.get(ModuleTable, 5)
    assert module
    module.Temporary_Locked = True
    ctx.session.flush()

    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Title": "Locked out"})

    assert response.status_code == 400
    assert response.json()["detail"] == "The module is locked"


@pytest.mark.parametrize(
    "module_id, detail",
    [
        pytest.param(3, "De module is gesloten", id="closed"),
        pytest.param(999999, "Module niet gevonden", id="unknown"),
    ],
)
def test_inaccessible_module_returns_404(admin: TestClient, module_id: int, detail: str):
    response: Response = admin.patch(f"/modules/{module_id}/object/beleidskeuze/1", json={"Title": "Not allowed"})

    assert response.status_code == 404
    assert response.json()["detail"] == detail


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("viewer", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission-and-not-owner"),
        pytest.param("admin", 200, None, id="role-with-permission"),
    ],
)
def test_permission_matrix(
    request: FixtureRequest,
    client_fixture: str,
    expected_status: int,
    expected_detail: Optional[str],
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    response: Response = test_client.patch("/modules/5/object/beleidskeuze/1", json={"Title": "Patched by a role"})

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail


@pytest.mark.parametrize(
    "lineage_id, expected_status",
    [
        pytest.param(510, 200, id="owner-of-the-object"),
        pytest.param(1, 401, id="not-owner-of-the-object"),
    ],
)
def test_owner_may_patch_without_the_role_permission(owner_1: TestClient, lineage_id: int, expected_status: int):
    response: Response = owner_1.patch(
        f"/modules/5/object/beleidskeuze/{lineage_id}", json={"Title": "Patched by the owner"}
    )

    assert response.status_code == expected_status, response.text
