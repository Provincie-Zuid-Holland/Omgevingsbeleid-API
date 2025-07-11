from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.core.tables.objects import ObjectsTable
from app.core.utils.utils import table_to_dict


class ObjectProvider:
    def __init__(
        self,
        object_repository: ObjectRepository,
        module_object_repository: ModuleObjectRepository,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository

    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[dict]:
        maybe_object: Optional[ObjectsTable] = self._object_repository.get_by_uuid(session, uuid)
        if maybe_object:
            return table_to_dict(maybe_object)

        maybe_module_object = self._module_object_repository.get_by_uuid(session, uuid)
        if maybe_module_object:
            return table_to_dict(maybe_module_object)

        return None
