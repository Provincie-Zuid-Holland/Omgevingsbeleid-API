import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api.domains.modules.endpoints.module_patch_object_endpoint import (
    _guard_target_codes_in_module_or_valid,
)
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.core.tables.modules import ModuleObjectsTable
from tests.conftest import Context

# beleidsdoel-1 is published/valid since march (see d070_objects_march.py).
# beleidsdoel-4 only ever exists as a draft in module 1 (see d201_module_1_basic.py), never published.
# maatregel-6 was valid but its End_Validity (2025-06-01) has passed, and it is not in any module.


def _guard(ctx: Context, module_id: int, target_codes: list[str]) -> None:
    _guard_target_codes_in_module_or_valid(
        ctx.session,
        ObjectRepository(),
        ModuleObjectRepository(),
        module_id,
        target_codes,
    )


def test_valid_object_is_allowed_regardless_of_module(ctx: Context):
    _guard(ctx, module_id=2, target_codes=["beleidsdoel-1"])


def test_draft_in_the_current_module_is_allowed(ctx: Context):
    _guard(ctx, module_id=1, target_codes=["beleidsdoel-4"])


def test_draft_in_another_module_is_rejected(ctx: Context):
    with pytest.raises(HTTPException) as exc_info:
        _guard(ctx, module_id=2, target_codes=["beleidsdoel-4"])

    assert exc_info.value.status_code == 400
    assert "beleidsdoel-4" in exc_info.value.detail


def test_object_that_is_neither_valid_nor_in_any_module_is_rejected(ctx: Context):
    with pytest.raises(HTTPException) as exc_info:
        _guard(ctx, module_id=1, target_codes=["maatregel-6"])

    assert exc_info.value.status_code == 400
    assert "maatregel-6" in exc_info.value.detail


def test_deleted_draft_in_the_current_module_is_rejected(ctx: Context):
    draft = ctx.session.scalars(
        select(ModuleObjectsTable)
        .where(ModuleObjectsTable.Module_ID == 1)
        .where(ModuleObjectsTable.Code == "beleidsdoel-4")
        .order_by(ModuleObjectsTable.Modified_Date.desc())
    ).first()
    assert draft is not None
    draft.Deleted = True
    ctx.session.flush()

    with pytest.raises(HTTPException) as exc_info:
        _guard(ctx, module_id=1, target_codes=["beleidsdoel-4"])

    assert exc_info.value.status_code == 400


def test_all_invalid_codes_are_reported_together(ctx: Context):
    with pytest.raises(HTTPException) as exc_info:
        _guard(ctx, module_id=2, target_codes=["beleidsdoel-1", "beleidsdoel-4", "maatregel-6"])

    detail = exc_info.value.detail
    assert "beleidsdoel-4" in detail
    assert "maatregel-6" in detail
    assert "beleidsdoel-1" not in detail
