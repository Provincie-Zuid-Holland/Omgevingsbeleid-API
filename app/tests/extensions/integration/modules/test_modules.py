import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from pydantic import ValidationError
from fastapi import HTTPException

from app.extensions.modules.models.models import (
    AllModuleStatusCode,
    ModuleObjectAction,
)
from app.extensions.modules.endpoints.create_module import (
    EndpointHandler as CreateEndpoint,
    ModuleCreate,
)
from app.extensions.modules.endpoints.module_add_new_object import (
    EndpointHandler as NewObjectEndpoint,
    ModuleAddNewObject,
    NewObjectStaticResponse,
)

from app.extensions.modules.endpoints.module_add_existing_object import (
    EndpointHandler as NewExistingObjectEndpoint,
    ModuleAddExistingObject,
)

from app.extensions.modules.endpoints.edit_module import (
    EndpointHandler as EditEndpoint,
    ModuleEdit,
)

from app.extensions.modules.endpoints.activate_module import (
    EndpointHandler as ActivateEndpoint,
)

from app.extensions.modules.endpoints.complete_module import (
    EndpointHandler as CompleteEndpoint,
    CompleteModule,
)
from unittest.mock import patch
from app.tests.helpers import patch_multiple
from .fixtures import (  # noqa
    local_tables,
    setup_db_once,
    db,
    engine,
    populate_users,
    populate_statics,
    populate_objects,
    populate_modules,
    ExtendedLocalTables,
    module_context_repo,
    module_status_repo,
    module_object_repo,
    object_provider,
)


class TestModulesEndpoints:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup(
        self, request, setup_db_once, populate_users, populate_statics, populate_objects
    ):  # noqa
        # timestamps
        request.cls.now = datetime.now()
        request.cls.five_days_ago = request.cls.now - timedelta(days=5)
        request.cls.five_days_later = request.cls.now + timedelta(days=5)

        # Factory data
        request.cls.super_user = populate_users[0]
        request.cls.ba_user = populate_users[2]
        request.cls.pf_user = populate_users[4]

        request.cls.object_statics = populate_statics
        request.cls.objects = populate_objects

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
            .filter(
                local_tables.ModuleStatusHistoryTable.Module_ID == response.Module_ID
            )
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
        self,
        db: Session,
        mock_permission_service,
        object_provider,
        module_context_repo,
        local_tables: ExtendedLocalTables,
    ):
        # Precondition state: existing module + objects
        existing_module = db.query(local_tables.ModuleTable).one()
        existing_object = next(
            obj for obj in self.objects if obj.Code == "beleidskeuze-3"
        )

        # Build request
        request_obj = ModuleAddExistingObject(
            Object_UUID=existing_object.UUID,
            Action=ModuleObjectAction.Edit,
            Explanation="monty",
            Conclusion="python",
        )
        endpoint = NewExistingObjectEndpoint(
            db=db,
            object_provider=object_provider,
            object_context_repository=module_context_repo,
            permission_service=mock_permission_service,
            allowed_object_types=["beleidskeuze"],
            user=self.ba_user,
            module=existing_module,
            object_in=request_obj,
        )

        # Execute
        base_path = "app.extensions.modules.endpoints.module_add_existing_object"
        objects_repo_path = "app.dynamic.repository.object_repository"
        with patch_multiple(
            patch(
                f"{base_path}.ModuleObjectContextTable",
                local_tables.ModuleObjectContextTable,
            ),
            patch(f"{base_path}.ModuleObjectsTable", local_tables.ModuleObjectsTable),
            patch(f"{base_path}.ModuleTable", local_tables.ModuleTable),
            patch(f"{objects_repo_path}.ObjectsTable", local_tables.ObjectsTable),
        ):
            response = endpoint.handle()

        # Response spec
        assert response.message == "OK"

        # Expect new module context object created
        new_module_obj = (
            db.query(local_tables.ModuleObjectsTable)
            .filter(local_tables.ModuleObjectsTable.Code == "beleidskeuze-3")
            .one()
        )
        assert new_module_obj is not None

        new_module_obj_context = (
            db.query(local_tables.ModuleObjectContextTable)
            .filter(local_tables.ModuleObjectContextTable.Code == "beleidskeuze-3")
            .one()
        )
        assert new_module_obj_context is not None
        assert new_module_obj_context.Action == ModuleObjectAction.Edit
        assert new_module_obj_context.Module_ID == existing_module.Module_ID

    def test_module_add_existing_object_update_context(
        self,
        db: Session,
        mock_permission_service,
        object_provider,
        module_context_repo,
        local_tables: ExtendedLocalTables,
    ):
        pass

    def test_module_edit(
        self,
        db: Session,
        mock_permission_service,
        local_tables: ExtendedLocalTables,
    ):
        # Precondition state: existing module
        existing_module = db.query(local_tables.ModuleTable).one()

        # Build request
        request_obj = ModuleEdit(
            Temporary_Locked=True,
            Title="changed title",
            Description="changed description",
            Module_Manager_1_UUID=self.super_user.UUID,
            Module_Manager_2_UUID=self.pf_user.UUID,
        )
        endpoint = EditEndpoint(
            db=db,
            permission_service=mock_permission_service,
            user=self.ba_user,
            module=existing_module,
            object_in=request_obj,
        )

        # Execute
        response = endpoint.handle()

        # Response spec
        assert response.message == "OK"

        db.refresh(existing_module)

        # Expect module edited
        assert all(
            getattr(existing_module, k) == v for k, v in request_obj.dict().items()
        ), "One or more attributes of changed module do not match the request"

    def test_module_activate_permission(
        self,
        db,
        mock_permission_service,
        mock_dispatcher,
        local_tables: ExtendedLocalTables,
    ):  # noqa
        existing_module = db.query(local_tables.ModuleTable).one()
        endpoint = ActivateEndpoint(
            db=db,
            permission_service=mock_permission_service,
            event_dispatcher=mock_dispatcher,
            user=self.ba_user,  # should fail for non-managers for module
            module=existing_module,
        )
        # Execute
        with pytest.raises(
            HTTPException, match="You are not allowed to modify this module"
        ):
            endpoint.handle()

    def test_module_activate(
        self,
        db,
        mock_permission_service,
        mock_dispatcher,
        local_tables: ExtendedLocalTables,
    ):  # noqa
        # Precondition state: existing module NOT activated
        existing_module = db.query(local_tables.ModuleTable).one()
        endpoint = ActivateEndpoint(
            db=db,
            permission_service=mock_permission_service,
            event_dispatcher=mock_dispatcher,
            user=self.super_user,
            module=existing_module,
        )

        # Execute
        base_path = "app.extensions.modules.endpoints.activate_module"
        with patch(
            f"{base_path}.ModuleStatusHistoryTable",
            local_tables.ModuleStatusHistoryTable,
        ):
            response = endpoint.handle()

        # Response spec
        assert response.message == "OK"

        # Assert changed module + status history
        db.refresh(existing_module)
        assert existing_module.Activated is True
        assert existing_module.status_history is not None
        assert existing_module.Status.Status == AllModuleStatusCode.Ontwerp_GS_Concept

    def test_module_complete(
        self,
        db,
        mock_dispatcher,
        module_object_repo,
        module_status_repo,
        local_tables: ExtendedLocalTables,
    ):
        """
        Preconditions for module to complete:
            - set to locked
            - status is 'vastgesteld'

        Results in:
            - module objects from previous states converted to "objects"
            - any validity options from request applied
            - module set to closed+succesful
            - status change event fired
        """
        # Status setup
        existing_module = db.query(local_tables.ModuleTable).one()
        new_status = local_tables.ModuleStatusHistoryTable(
            Module_ID=existing_module.Module_ID,
            Status=AllModuleStatusCode.Vastgesteld.value,
            Created_Date=datetime.now(),
            Created_By_UUID=self.super_user.UUID,
        )
        existing_module.status_history.append(new_status)
        db.add(existing_module)
        db.commit()

        # Build request
        osg = []
        request_obj = CompleteModule(
            IDMS_Link="https://mock-me-a-idms.link",
            Decision_Number="mock-me-a-string",
            Link_To_Decision_Document="mock-me-a-link",
            ObjectSpecifiekeGeldigheden=osg,
        )

        endpoint = CompleteEndpoint(
            db=db,
            module_status_repository=module_status_repo,
            module_object_repository=module_object_repo,
            event_dispatcher=mock_dispatcher,
            user=self.super_user,
            module=existing_module,
            object_in=request_obj,
        )

        # Execute
        base_path = "app.extensions.modules.endpoints.complete_module"
        module_object_repo = (
            "app.extensions.modules.repository.module_object_repository"
        )
        with patch_multiple(
            patch(f"{base_path}.ObjectsTable", local_tables.ObjectsTable),
            patch(f"{base_path}.ModuleObjectsTable", local_tables.ModuleObjectsTable),
            patch(
                f"{module_object_repo}.ModuleObjectsTable",
                local_tables.ModuleObjectsTable,
            ),
        ):
            response = endpoint.handle()

        # assert
        assert response.message == "OK"

        # ensure db state as expected
        db.refresh(existing_module)
        assert existing_module.Closed is True
        assert existing_module.Status.Status == "Module afgerond"

        objects_created = (
            db.query(local_tables.ObjectsTable)
            .filter(
                or_(
                    local_tables.ObjectsTable.Code == "ambitie-1",
                    local_tables.ObjectsTable.Code == "ambitie-2",
                )
            )
            .all()
        )
        assert (
            len(objects_created) == 2
        ), "Expected 2 objects to be created on completion"
