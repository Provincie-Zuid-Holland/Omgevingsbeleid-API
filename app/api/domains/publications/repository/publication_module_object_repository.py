from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleObjectsTable


class PublicationModuleObjectRepository(BaseRepository):
    def get_by_module_id(self, session: Session, module_id: int) -> List[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .options(selectinload(ModuleObjectsTable.ObjectStatics))
            .filter(ModuleObjectsTable.Module_ID == module_id)
        )
        return self.fetch_all(session, stmt)
