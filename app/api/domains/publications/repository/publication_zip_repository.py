from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.api.base_repository import BaseRepository
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationPackageZipTable,
)


class PublicationZipRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> PublicationPackageZipTable | None:
        stmt = select(PublicationPackageZipTable).filter(PublicationPackageZipTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_by_act_package_id(self, session: AsyncSession, idx: UUID) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .options(undefer(PublicationPackageZipTable.binary))
            .join(PublicationActPackageTable)
            .filter(PublicationActPackageTable.id == idx)
        )
        return await self.fetch_first(session, stmt)

    async def get_by_announcement_package_id(
        self, session: AsyncSession, idx: UUID
    ) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .options(undefer(PublicationPackageZipTable.binary))
            .join(PublicationAnnouncementPackageTable)
            .filter(PublicationAnnouncementPackageTable.id == idx)
        )
        return await self.fetch_first(session, stmt)
