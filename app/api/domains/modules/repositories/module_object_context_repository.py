from typing import Optional

from sqlalchemy import select

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleObjectContextTable


class ModuleObjectContextRepository(BaseRepository):
    def get_by_ids(self, module_id: int, object_type: str, object_id: int) -> Optional[ModuleObjectContextTable]:
        stmt = (
            select(ModuleObjectContextTable)
            .filter(ModuleObjectContextTable.Object_Type == object_type)
            .filter(ModuleObjectContextTable.Object_ID == object_id)
            .filter(ModuleObjectContextTable.Module_ID == module_id)
        )

        maybe_context: Optional[ModuleObjectContextTable] = self._db.scalars(stmt).first()
        return maybe_context
