from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.dynamic.repository.repository import BaseRepository
from app.extensions.attachments.db.tables import StorageFileTable


class StorageFileRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[StorageFileTable]:
        stmt = select(StorageFileTable).filter(StorageFileTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_checksum_uuid(self, checksum: str) -> Optional[StorageFileTable]:
        lookup: str = checksum[0:10]
        stmt = (
            select(StorageFileTable)
            .filter(StorageFileTable.Lookup == lookup)
            .filter(StorageFileTable.Checksum == checksum)
        )
        return self.fetch_first(stmt)
