from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleStatusHistoryTable


class ModuleStatusRepository(BaseRepository):
    async def get_all_by_module_id(self, session: AsyncSession, module_id: int) -> list[ModuleStatusHistoryTable]:
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.module_id == module_id)
            .order_by(asc(ModuleStatusHistoryTable.id))
        )
        statuses: list[ModuleStatusHistoryTable] = (await session.scalars(stmt)).all()
        return statuses

    async def get_by_id(self, session: AsyncSession, module_id: int, status_id: int) -> ModuleStatusHistoryTable | None:
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.id == status_id)
            .filter(ModuleStatusHistoryTable.module_id == module_id)
        )
        maybe_status = (await session.scalars(stmt)).first()
        return maybe_status

    async def get_latest_for_module(self, session: AsyncSession, module_id: int) -> ModuleStatusHistoryTable | None:
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.module_id == module_id)
            .order_by(desc(ModuleStatusHistoryTable.created_date))
        )
        maybe_status = (await session.scalars(stmt)).first()

        return maybe_status
