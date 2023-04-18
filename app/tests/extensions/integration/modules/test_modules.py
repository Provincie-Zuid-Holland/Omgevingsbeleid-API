import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.extensions.modules.endpoints.create_module import (
    EndpointHandler as CreateEndpoint,
    ModuleCreate,
    ModuleCreatedResponse,
)
from app.extensions.modules.endpoints.module_add_new_object import (
    EndpointHandler as NewObjectEndpoint,
    ModuleAddNewObject,
    NewObjectStaticResponse,
)
from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
    ObjectFixtureFactory,
    ModuleFixtureFactory,
)
from unittest.mock import patch
from app.tests.helpers import patch_multiple
from .fixtures import (  # noqa
    local_tables,
    setup_db,
    db,
    engine,
    populate_users,
    populate_statics,
    populate_modules,
    ExtendedLocalTables,
)


class TestModulesEndpoints:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request, setup_db, populate_users, populate_statics):  # noqa
        # timestamps
        request.cls.now = datetime.now()
        request.cls.five_days_ago = request.cls.now - timedelta(days=5)
        request.cls.five_days_later = request.cls.now + timedelta(days=5)

        # Factory data
        request.cls.super_user = populate_users[0]
        request.cls.ba_user = populate_users[2]

        request.cls.module_request = ModuleCreate(
            Title="monty",
            Description="python",
            Module_Manager_1_UUID=request.cls.ba_user.UUID,
        )
        yield

    def test_module_create(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        endpoint = CreateEndpoint(
            db=db, user=self.ba_user, object_in=self.module_request
        )
        # Create module
        response = endpoint.handle()

        # Test Module and History created in DB
        assert response.Module_ID == 1
        new_module = (
            db.query(local_tables.ModuleTable)
            .filter(local_tables.ModuleTable.Module_ID == response.Module_ID)
            .one()
        )
        assert new_module is not None

        new_history = (
            db.query(local_tables.ModuleStatusHistoryTable)
            .filter(local_tables.ModuleStatusHistoryTable.ID == 1)
            .filter(local_tables.ModuleStatusHistoryTable.Module_ID == response.Module_ID)
            .one()
        )
        assert new_history is not None

    def test_module_duplicate_manager(self, local_tables: ExtendedLocalTables):  # noqa
        with pytest.raises(ValidationError):
            ModuleCreate(
                Title="monty",
                Description="python",
                Module_Manager_1_UUID=self.ba_user.UUID,
                Module_Manager_2_UUID=self.ba_user.UUID,
            )

    def test_module_new_object(
        self, db, mock_permission_service, local_tables: ExtendedLocalTables
    ):  # noqa
        existing_module = db.query(local_tables.ModuleTable).one()
        request_obj = ModuleAddNewObject(
            Object_Type="beleidskeuze",
            Title="monty",
            Owner_1_UUID=self.ba_user.UUID,
            Explanation="python",
            Conclusion="python",
        )
        base_path = "app.extensions.modules.endpoints.module_add_new_object"
        with patch_multiple(
            patch(f"{base_path}.ObjectStaticsTable", local_tables.ObjectStaticsTable),
            patch(
                f"{base_path}.ModuleObjectContextTable",
                local_tables.ModuleObjectContextTable,
            ),
            patch(f"{base_path}.ModuleObjectsTable", local_tables.ModuleObjectsTable),
        ):
            endpoint = NewObjectEndpoint(
                db=db,
                allowed_object_types=["beleidskeuze"],
                permission_service=mock_permission_service,
                user=self.ba_user,
                module=existing_module,
                object_in=request_obj,
            )
            response: NewObjectStaticResponse = endpoint.handle()

        # Expect has_permission not called as user is_manager
        assert len(mock_permission_service.calls) == 0

        # Response spec
        assert response.Object_Type == "beleidskeuze"
        assert response.Object_ID == 4

        # Ensure DB objects created
        new_static = (
            db.query(local_tables.ObjectStaticsTable)
            .filter(local_tables.ObjectStaticsTable.Code == "beleidskeuze-4")
            .one()
        )
        assert new_static is not None

        new_module_obj = (
            db.query(local_tables.ModuleObjectsTable)
            .filter(local_tables.ModuleObjectsTable.Code == "beleidskeuze-4")
            .one()
        )
        assert new_module_obj is not None

        new_module_obj_context = (
            db.query(local_tables.ModuleObjectContextTable)
            .filter(local_tables.ModuleObjectContextTable.Code == "beleidskeuze-4")
            .one()
        )
        assert new_module_obj_context is not None

    def test_module_add_existing_object(
        self, db, mock_permission_service, local_tables: ExtendedLocalTables
    ):  # noqa
        pass

    def test_module_edit(
        self, db, mock_permission_service, local_tables: ExtendedLocalTables
    ):  # noqa
        pass

    def test_module_activate(
        self, db, mock_permission_service, local_tables: ExtendedLocalTables
    ):  # noqa
        pass

    def test_module_complete(
        self, db, mock_permission_service, local_tables: ExtendedLocalTables
    ):  # noqa
        pass
