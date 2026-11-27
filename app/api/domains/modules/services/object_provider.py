from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_by_id(self, session: AsyncSession, idx: UUID) -> dict | None:
        maybe_object: ObjectsTable | None = await self._object_repository.get_by_id(session, idx)
        if maybe_object:
            return table_to_dict(maybe_object)

        maybe_module_object = await self._module_object_repository.get_by_id(session, idx)
        if maybe_module_object:
            return table_to_dict(maybe_module_object)

        return None
