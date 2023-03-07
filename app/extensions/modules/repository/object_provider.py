from typing import Optional
from uuid import UUID
from app.dynamic.db.objects_table import ObjectsTable

from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)


class ObjectProvider:
    def __init__(
        self,
        object_repository: ObjectRepository,
        module_object_repository: ModuleObjectRepository,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._module_object_repository: ModuleObjectRepository = (
            module_object_repository
        )

    def get_by_uuid(self, uuid: UUID) -> Optional[dict]:
        maybe_object: Optional[ObjectsTable] = self._object_repository.get_by_uuid(uuid)
        if maybe_object:
            return self._as_dict(maybe_object)

        maybe_module_object = self._module_object_repository.get_by_uuid(uuid)
        if maybe_module_object:
            return self._as_dict(maybe_module_object)

        return None

    def _as_dict(self, object_table) -> dict:
        object_dict = dict(object_table.__dict__)
        object_dict.pop("_sa_instance_state", None)
        return object_dict
