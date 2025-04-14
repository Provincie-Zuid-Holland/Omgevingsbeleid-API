from typing import List, Optional

from sqlalchemy import desc, select

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleStatusHistoryTable


class ModuleStatusRepository(BaseRepository):
    def get_all_by_module_id(self, module_id: int) -> List[ModuleStatusHistoryTable]:
        stmt = select(ModuleStatusHistoryTable).filter(ModuleStatusHistoryTable.Module_ID == module_id)
        statuses: List[ModuleStatusHistoryTable] = self._db.scalars(stmt).all()
        return statuses

    def get_by_id(self, module_id: int, status_id: int) -> Optional[ModuleStatusHistoryTable]:
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.ID == status_id)
            .filter(ModuleStatusHistoryTable.Module_ID == module_id)
        )
        maybe_status = self._db.scalars(stmt).first()
        return maybe_status

    def get_latest_for_module(self, module_id: int) -> Optional[ModuleStatusHistoryTable]:
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.Module_ID == module_id)
            .order_by(desc(ModuleStatusHistoryTable.Created_Date))
        )
        maybe_status = self._db.scalars(stmt).first()

        return maybe_status
