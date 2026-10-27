from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.core.tables.publications import PublicationStorageFileTable, PublicationVersionAttachmentTable


class PublicationVersionAttachmentRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: int) -> PublicationVersionAttachmentTable | None:
        stmt = (
            select(PublicationVersionAttachmentTable)
            .options(selectinload(PublicationVersionAttachmentTable.file))
            .filter(PublicationVersionAttachmentTable.id == idx)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_binary(self, session: AsyncSession, idx: int) -> PublicationVersionAttachmentTable | None:
        stmt = (
            select(PublicationVersionAttachmentTable)
            .options(selectinload(PublicationVersionAttachmentTable.file).undefer(PublicationStorageFileTable.binary))
            .filter(PublicationVersionAttachmentTable.id == idx)
        )
        return await self.fetch_first(session, stmt)

    async def get_by_version_id(
        self, session: AsyncSession, version_id: UUID
    ) -> list[PublicationVersionAttachmentTable]:
        stmt = select(PublicationVersionAttachmentTable).filter(
            PublicationVersionAttachmentTable.publication_version_id == version_id
        )
        return await self.fetch_all(session, stmt)

    async def get_by_version_id_with_binary(
        self, session: AsyncSession, version_id: UUID
    ) -> list[PublicationVersionAttachmentTable]:
        stmt = (
            select(PublicationVersionAttachmentTable)
            .options(selectinload(PublicationVersionAttachmentTable.file).undefer(PublicationStorageFileTable.binary))
            .filter(PublicationVersionAttachmentTable.publication_version_id == version_id)
            .order_by(PublicationVersionAttachmentTable.id)
        )
        return await self.fetch_all(session, stmt)

    async def get_all(self, session: AsyncSession):
        stmt = select(PublicationVersionAttachmentTable)
        return await self.fetch_all(session, stmt)
