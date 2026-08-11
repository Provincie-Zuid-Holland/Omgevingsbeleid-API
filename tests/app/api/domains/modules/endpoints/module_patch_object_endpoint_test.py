import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from pytest import FixtureRequest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from tests.conftest import Context
from tests.fixtures.internal.spec.modules import ModuleBeleidskeuzeSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import Ref


def _fetch_draft(session: Session, draft_uuid: uuid.UUID) -> ModuleObjectsTable:
    draft: ModuleObjectsTable | None = session.get(ModuleObjectsTable, draft_uuid)
    assert draft
    return draft


def _assert_same_datetime(actual: datetime, expected: datetime | None = None):
    expected = expected or datetime.now(UTC)
    difference: timedelta = abs(actual.replace(tzinfo=None) - expected.replace(tzinfo=None))
    assert difference <= timedelta(milliseconds=1), f"{actual} differs {difference} from {expected}"


def test_patch_adds_a_new_draft_to_the_lineage(admin: TestClient, ctx: Context):
    previous_draft: ModuleBeleidskeuzeSpec = ctx.f.find(
        Ref(ModuleBeleidskeuzeSpec, "mod_5_beleidskeuze_1_first_entry")
    ).spec
    admin_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(UserSpec, "admin"))

    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={"Title": "Patched via module 5"})

    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
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

    all_drafts: list[ModuleObjectsTable] = list(
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

    object_static: ObjectStaticsTable | None = ctx.session.get(ObjectStaticsTable, draft.Code)
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
        pytest.param({"Hierarchy_Code": "beleidsdoel-999999"}, "Hierarchy_Code", id="code-that-does-not-exist"),
        pytest.param({"Gebiedengroep_Code": "beleidsdoel-1"}, "Gebiedengroep_Code", id="wrong-type-for-gebiedengroep"),
    ],
)
def test_invalid_body_returns_422(admin: TestClient, payload: dict[str, Any], invalid_field: str):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json=payload)

    assert response.status_code == 422, response.text
    assert invalid_field in {error["loc"][-1] for error in response.json()["detail"]}


@pytest.mark.parametrize(
    "target_codes",
    [
        pytest.param(["gebied-2"], id="vigerend-gebied"),
        pytest.param(["gebiedengroep-1"], id="vigerend-gebiedengroep"),
        pytest.param(["gebied-510", "gebiedengroep-510"], id="created-in-this-module"),
        pytest.param(["gebied-2", "gebied-510"], id="vigerend-and-created-in-this-module"),
        pytest.param(["gebied-3"], id="terminate-that-was-removed-from-the-module"),
    ],
)
def test_target_codes_accepts_vigerend_and_own_module_codes(admin: TestClient, ctx: Context, target_codes: list[str]):
    response: Response = admin.patch("/modules/5/object/gebiedsaanwijzing/510", json={"Target_Codes": target_codes})

    assert response.status_code == 200, response.text
    new_draft: ModuleObjectsTable = _fetch_draft(ctx.session, uuid.UUID(response.json()["UUID"]))
    assert new_draft.Target_Codes == target_codes


@pytest.mark.parametrize(
    "target_codes, invalid_codes",
    [
        pytest.param(["gebied-610"], ["gebied-610"], id="created-in-another-module"),
        pytest.param(["gebied-511"], ["gebied-511"], id="hidden-in-this-module"),
        pytest.param(["gebied-1"], ["gebied-1"], id="terminated-in-this-module"),
        pytest.param(["gebied-4"], ["gebied-4"], id="end-validity-in-the-past"),
        pytest.param(["gebied-5"], ["gebied-5"], id="start-validity-in-the-future"),
        pytest.param(["gebied-999999"], ["gebied-999999"], id="does-not-exist"),
        pytest.param(["gebied-2", "gebied-610"], ["gebied-610"], id="only-the-invalid-code-is-reported"),
    ],
)
def test_target_codes_rejects_codes_not_usable_in_the_module(
    admin: TestClient, target_codes: list[str], invalid_codes: list[str]
):
    response: Response = admin.patch("/modules/5/object/gebiedsaanwijzing/510", json={"Target_Codes": target_codes})

    assert response.status_code == 422, response.text
    errors: list[dict[str, Any]] = [error for error in response.json()["detail"] if error["loc"][-1] == "Target_Codes"]
    assert len(errors) == 1
    message: str = errors[0]["msg"]
    for invalid_code in invalid_codes:
        assert invalid_code in message
    for valid_code in set(target_codes) - set(invalid_codes):
        assert valid_code not in message


@pytest.mark.parametrize(
    "module_id, lineage_id, target_codes, expected_status",
    [
        pytest.param(5, 510, ["gebied-510"], 200, id="module-5-with-its-own-code"),
        pytest.param(5, 510, ["gebied-610"], 422, id="module-5-with-the-code-of-module-6"),
        pytest.param(6, 610, ["gebied-610"], 200, id="module-6-with-its-own-code"),
        pytest.param(6, 610, ["gebied-510"], 422, id="module-6-with-the-code-of-module-5"),
        pytest.param(5, 510, ["gebied-1"], 422, id="module-5-terminates-a-vigerend-code"),
        pytest.param(6, 610, ["gebied-1"], 200, id="module-6-does-not-terminate-it"),
    ],
)
def test_target_codes_are_scoped_to_the_patched_module(
    admin: TestClient,
    module_id: int,
    lineage_id: int,
    target_codes: list[str],
    expected_status: int,
):
    response: Response = admin.patch(
        f"/modules/{module_id}/object/gebiedsaanwijzing/{lineage_id}", json={"Target_Codes": target_codes}
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.parametrize(
    "target_codes, expected_message",
    [
        pytest.param([], "Missing required value", id="empty-list"),
        pytest.param(None, "Missing required value", id="null"),
        pytest.param(["beleidskeuze-1"], "Invalid object type", id="object-type-that-is-not-allowed"),
    ],
)
def test_target_codes_rejects_invalid_values(
    admin: TestClient, target_codes: list[str] | None, expected_message: str
):
    response: Response = admin.patch("/modules/5/object/gebiedsaanwijzing/510", json={"Target_Codes": target_codes})

    assert response.status_code == 422, response.text
    errors: list[dict[str, Any]] = [error for error in response.json()["detail"] if error["loc"][-1] == "Target_Codes"]
    assert len(errors) == 1
    assert expected_message in errors[0]["msg"]


def test_lineage_outside_the_module_returns_404(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/3", json={"Title": "Not in this module"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Module object niet gevonden"


def test_empty_body_returns_400(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Niets om aan te passen"


def test_unknown_lineage_returns_404(admin: TestClient):
    response: Response = admin.patch("/modules/5/object/beleidskeuze/999999", json={"Title": "Does not exist"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Object static niet gevonden"


def test_locked_module_returns_400(admin: TestClient, ctx: Context):
    module: ModuleTable | None = ctx.session.get(ModuleTable, 5)
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
    expected_detail: str | None,
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
