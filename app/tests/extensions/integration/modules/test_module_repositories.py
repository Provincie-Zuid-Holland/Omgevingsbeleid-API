from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.dynamic.dependencies import FilterObjectCode
from app.extensions.modules.repository import ModuleRepository
from app.tests.fixture_factories import (
    ModuleFixtureFactory,
    UserFixtureFactory,
)
from app.tests.helpers import patch_multiple

from .fixtures import (
    ExtendedLocalTables,
    local_tables,  # noqa
    module_context_repo,
    module_object_repo,
    module_repo,
    setup_db,
)


class TestModuleRepository:
    """
    Integration tests to ensure module db querying behaves as
    expected.
    """

    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables, setup_db):  # noqa
        # timestamps
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]
        self.pf_user = self.user_factory.objects[4]

        mf = ModuleFixtureFactory(db, local_tables)
        mf.create_all_modules()
        mf.create_all_module_status_history()
        mf.create_all_module_object_context()
        mf.create_all_module_objects()
        mf.populate_db()

        self.module_factory = mf

    def test_module_get_by_id(
        self,
        module_repo: ModuleRepository,
        db: Session,
        local_tables: ExtendedLocalTables,
    ):  # noqa
        mod = self.module_factory.modules[0]  # Module A in factory
        result = module_repo.get_by_id(mod.Module_ID)
        assert result is not None
        assert result.Activated == 1
        assert result.Title == "Fixture module A"

    def test_module_get_by_id_invalid(
        self,
        module_repo: ModuleRepository,
        db: Session,
        local_tables: ExtendedLocalTables,
    ):  # noqa
        NON_EXISTING_ID = 999
        result = module_repo.get_by_id(NON_EXISTING_ID)
        assert result is None

    def test_module_get_with_filters_only_active(
        self,
        module_repo: ModuleRepository,
        db: Session,
        local_tables: ExtendedLocalTables,
    ):
        # setup closed module
        closed = {
            "Module_ID": 1000,
            "Title": "inactive",
            "Description": "inactive",
            "Module_Manager_1_UUID": self.ba_user.UUID,
            "Created_By_UUID": self.ba_user.UUID,
            "Modified_By_UUID": self.ba_user.UUID,
            "Activated": 0,
            "Closed": 1,
            "Successful": 0,
            "Temporary_Locked": 0,
        }
        mod = self.module_factory._create_module(closed)
        db.add(mod)
        db.commit()

        result = module_repo.get_with_filters(
            only_active=True, object_code=None, mine=None
        )
        assert result is not None
        for module in result:
            assert module.Closed != 1

    def test_module_get_with_filters_only_mine(
        self,
        module_repo: ModuleRepository,
        db: Session,
        local_tables: ExtendedLocalTables,
    ):
        pf_user_owned = {
            "Module_ID": 1005,
            "Title": "the life of brian",
            "Description": "python",
            "Module_Manager_1_UUID": self.pf_user.UUID,
            "Created_By_UUID": self.pf_user.UUID,
            "Modified_By_UUID": self.pf_user.UUID,
            "Activated": 1,
            "Closed": 0,
            "Successful": 0,
            "Temporary_Locked": 0,
        }
        mod = self.module_factory._create_module(pf_user_owned)
        db.add(mod)
        db.commit()

        base_path = "app.extensions.modules.repository.module_repository"
        with patch_multiple(
            patch(f"{base_path}.ObjectStaticsTable", local_tables.ObjectStaticsTable),
            patch(
                f"{base_path}.ModuleObjectContextTable",
                local_tables.ModuleObjectContextTable,
            ),
            patch(f"{base_path}.ModuleObjectsTable", local_tables.ModuleObjectsTable),
            patch(f"{base_path}.ModuleTable", local_tables.ModuleTable),
        ):
            result = module_repo.get_with_filters(
                only_active=False, object_code=None, mine=self.pf_user.UUID
            )

        assert result is not None
        for module in result:
            assert any(
                condition == True
                for condition in [
                    module.Module_Manager_1_UUID == self.pf_user.UUID,
                    module.Module_Manager_2_UUID == self.pf_user.UUID,
                ]
            )

    def test_module_get_with_filters_code(
        self,
        module_repo: ModuleRepository,
        db: Session,
        local_tables: ExtendedLocalTables,
    ):
        mod = self.module_factory.modules[0]  # Module A in factory
        code_filter = FilterObjectCode(
            object_type="ambitie", lineage_id=mod.Module_ID
        )  # "ambitie-1"

        base_path = "app.extensions.modules.repository.module_repository"
        with patch_multiple(
            patch(f"{base_path}.ObjectStaticsTable", local_tables.ObjectStaticsTable),
            patch(
                f"{base_path}.ModuleObjectContextTable",
                local_tables.ModuleObjectContextTable,
            ),
            patch(f"{base_path}.ModuleObjectsTable", local_tables.ModuleObjectsTable),
            patch(f"{base_path}.ModuleTable", local_tables.ModuleTable),
        ):
            result = module_repo.get_with_filters(
                only_active=False, object_code=code_filter, mine=None
            )

        assert len(result) == 3


class TestModuleObjectRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables, setup_db):  # noqa
        # timestamps
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]
        self.pf_user = self.user_factory.objects[4]

        mf = ModuleFixtureFactory(db, local_tables)
        mf.create_all_modules()
        mf.create_all_module_status_history()
        mf.create_all_module_object_context()
        mf.create_all_module_objects()
        mf.populate_db()

        self.module_factory = mf
