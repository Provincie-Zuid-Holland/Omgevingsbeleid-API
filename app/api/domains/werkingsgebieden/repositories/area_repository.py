from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.api.base_repository import BaseRepository
from app.core.tables.others import AreasTable


class AreaRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> AreasTable | None:
        stmt = select(AreasTable).filter(AreasTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_by_source_uuid(self, session: AsyncSession, werkingsgebied_id: UUID) -> AreasTable | None:
        stmt = select(AreasTable).filter(AreasTable.source_uuid == werkingsgebied_id)
        return await self.fetch_first(session, stmt)

    async def get_by_source_hash_and_title(
        self, session: AsyncSession, source_hash: str, source_title: str
    ) -> AreasTable | None:
        if not source_hash:
            return None

        lookup: str = source_hash[0:10]
        stmt = (
            select(AreasTable)
            .filter(AreasTable.source_geometry_index == lookup)
            .filter(AreasTable.source_geometry_hash == source_hash)
            .filter(AreasTable.source_title == source_title)
        )
        return await self.fetch_first(session, stmt)

    async def get_by_source_hash(self, session: AsyncSession, source_hash: str) -> AreasTable | None:
        if not source_hash:
            return None

        lookup: str = source_hash[0:10]
        stmt = (
            select(AreasTable)
            .filter(AreasTable.source_geometry_index == lookup)
            .filter(AreasTable.source_geometry_hash == source_hash)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_gml(self, session: AsyncSession, idx: UUID) -> AreasTable | None:
        stmt = select(AreasTable).options(undefer(AreasTable.gml)).filter(AreasTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_many_with_gml(self, session: AsyncSession, ids: list[UUID]) -> list[AreasTable]:
        if len(ids) == 0:
            return []

        stmt = select(AreasTable).options(undefer("Gml")).filter(AreasTable.id.in_(ids))
        return await self.fetch_all(session, stmt)
