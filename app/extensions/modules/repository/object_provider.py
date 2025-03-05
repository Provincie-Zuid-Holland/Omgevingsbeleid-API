from typing import List, Optional
from uuid import UUID

from app.core.utils.utils import table_to_dict
from app.dynamic.db import ObjectsTable
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.modules.repository.module_object_repository import (
    LatestObjectPerModuleResult,
    ModuleObjectRepository,
)


class ObjectProvider:
    def __init__(
        self,
        object_repository: ObjectRepository,
        module_object_repository: ModuleObjectRepository,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository

    def get_by_uuid(self, uuid: UUID) -> Optional[dict]:
        maybe_object: Optional[ObjectsTable] = self._object_repository.get_by_uuid(uuid)
        if maybe_object:
            return table_to_dict(maybe_object)

        maybe_module_object = self._module_object_repository.get_by_uuid(uuid)
        if maybe_module_object:
            return table_to_dict(maybe_module_object)

        return None

    # TODO: unused?
    def list_object_versions_in_progress(self, object_uuid: UUID):
        minimum_status = ModuleStatusCode.Ontwerp_PS

        valid_obj = self._object_repository.get_by_uuid(object_uuid)

        if valid_obj is None:
            raise ValueError(f"No valid object found for UUID: {object_uuid}")

        return self._module_object_repository.get_latest_filtered(
            code=valid_obj.Code, minimum_status=minimum_status, is_active=True
        )

    def list_all_objects_related_to_werkingsgebied(self, werkingsgebied_code: str):
        """get all objects and latest version of active module objects related to a specified werkingsgebied."""
        regular_objects: List[ObjectsTable] = self._object_repository.get_all_latest_by_werkingsgebied(
            werkingsgebied_code
        )
        module_objects: List[LatestObjectPerModuleResult] = (
            self._module_object_repository.get_latest_versions_by_werkingsgebied(werkingsgebied_code)
        )
        return regular_objects + module_objects
