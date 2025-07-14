from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleObjectContextTable


class ModuleObjectContextRepository(BaseRepository):
    def get_by_ids(
        self, session: Session, module_id: int, object_type: str, object_id: int
    ) -> Optional[ModuleObjectContextTable]:
        stmt = (
            select(ModuleObjectContextTable)
            .filter(ModuleObjectContextTable.Object_Type == object_type)
            .filter(ModuleObjectContextTable.Object_ID == object_id)
            .filter(ModuleObjectContextTable.Module_ID == module_id)
        )

        maybe_context: Optional[ModuleObjectContextTable] = session.scalars(stmt).first()
        return maybe_context
