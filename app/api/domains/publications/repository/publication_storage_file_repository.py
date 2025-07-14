from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.publications import PublicationStorageFileTable


class PublicationStorageFileRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: UUID) -> Optional[PublicationStorageFileTable]:
        stmt = select(PublicationStorageFileTable).filter(PublicationStorageFileTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_by_checksum_uuid(self, session: Session, checksum: str) -> Optional[PublicationStorageFileTable]:
        lookup: str = checksum[0:10]
        stmt = (
            select(PublicationStorageFileTable)
            .filter(PublicationStorageFileTable.Lookup == lookup)
            .filter(PublicationStorageFileTable.Checksum == checksum)
        )
        return self.fetch_first(session, stmt)
