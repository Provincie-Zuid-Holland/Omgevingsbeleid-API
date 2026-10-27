from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.core.tables.publications import PublicationStorageFileTable


class PublicationStorageFileRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> PublicationStorageFileTable | None:
        stmt = select(PublicationStorageFileTable).filter(PublicationStorageFileTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_by_checksum(self, session: AsyncSession, checksum: str) -> PublicationStorageFileTable | None:
        lookup: str = checksum[0:10]
        stmt = (
            select(PublicationStorageFileTable)
            .filter(PublicationStorageFileTable.lookup == lookup)
            .filter(PublicationStorageFileTable.checksum == checksum)
        )
        return await self.fetch_first(session, stmt)

    async def get_all(self, session: AsyncSession):
        stmt = select(PublicationStorageFileTable)
        return await self.fetch_all(session, stmt)
