from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.dynamic.repository.repository import BaseRepository
from app.extensions.publications.tables.tables import PublicationStorageFileTable


class PublicationStorageFileRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[PublicationStorageFileTable]:
        stmt = select(PublicationStorageFileTable).filter(PublicationStorageFileTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_checksum_uuid(self, checksum: str) -> Optional[PublicationStorageFileTable]:
        lookup: str = checksum[0:10]
        stmt = (
            select(PublicationStorageFileTable)
            .filter(PublicationStorageFileTable.Lookup == lookup)
            .filter(PublicationStorageFileTable.Checksum == checksum)
        )
        return self.fetch_first(stmt)
