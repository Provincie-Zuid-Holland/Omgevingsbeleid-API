import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.tests.extensions.integration.modules.fixtures import ExtendedTableFactory
from app.tests.fixture_factories.objects_factory import ObjectFixtureFactory
from app.extensions.modules.models.models import (
    ModuleObjectAction,
)

from app.extensions.modules.endpoints.module_add_new_object import (
    EndpointHandler as NewObjectEndpoint,
    ModuleAddNewObject,
)
from app.extensions.modules.endpoints.module_add_existing_object import (
    EndpointHandler as NewExistingObjectEndpoint,
    ModuleAddExistingObject,
)


# local mock permissions
def mock_guard_valid_user(result=True):
    return result


def mock_guard_module_not_locked(result=True):
    return result


class TestModuleAddExistingObject:
    @patch(
        "app.extensions.modules.permissions.guard_valid_user", new=mock_guard_valid_user
    )
    @patch(
        "app.extensions.modules.permissions.guard_module_not_locked",
        new=mock_guard_module_not_locked,
    )
    def test_invalid_object_type(self):
        mock_tables = ExtendedTableFactory().local_tables
        of = ObjectFixtureFactory(local_tables=mock_tables)
        of.create_all_objects()  # create objects, no db interaction

        test_allowed_type = "beleidskeuze"

        # select object with wrong object_type
        amb_2 = of.objects[1]
        assert amb_2.Object_Type != test_allowed_type

        mock_provider = MagicMock()
        mock_provider.get_by_uuid = MagicMock(return_value=amb_2)

        request_obj = ModuleAddExistingObject(
            Object_UUID=uuid4(),
            Action=ModuleObjectAction.Edit,
            Explanation="monty",
            Conclusion="python",
        )

        endpoint = NewExistingObjectEndpoint(
            db=MagicMock(),
            object_provider=mock_provider,
            object_context_repository=MagicMock(),
            allowed_object_types=[test_allowed_type],
            permission_service=MagicMock(),
            user=MagicMock(),
            module=MagicMock(),
            object_in=request_obj,
        )

        with pytest.raises(HTTPException):
            endpoint.handle()


class TestModuleAddNewObject:
    @patch(
        "app.extensions.modules.permissions.guard_valid_user", new=mock_guard_valid_user
    )
    @patch(
        "app.extensions.modules.permissions.guard_module_not_locked",
        new=mock_guard_module_not_locked,
    )
    def test_invalid_object_type(self):
        test_allowed_type = "beleidskeuze"

        request_obj = ModuleAddNewObject(
            Object_Type="ambitie",
            Title="monty",
            Owner_1_UUID=uuid4(),
            Explanation="python",
            Conclusion="python",
        )

        endpoint = NewObjectEndpoint(
            db=MagicMock(),
            allowed_object_types=[test_allowed_type],
            permission_service=MagicMock(),
            user=MagicMock(),
            module=MagicMock(),
            object_in=request_obj,
        )

        with pytest.raises(HTTPException) as e:
            endpoint.handle()
