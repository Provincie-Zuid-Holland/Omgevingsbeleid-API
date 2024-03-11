from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.dynamic.repository.repository import BaseRepository
from app.extensions.publications.tables.tables import PublicationPackageTable, PublicationPackageZipTable


class PublicationZipRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[PublicationPackageZipTable]:
        stmt = select(PublicationPackageZipTable).filter(PublicationPackageZipTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_package_uuid(self, uuidx: UUID) -> Optional[PublicationPackageZipTable]:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationPackageTable)
            .filter(PublicationPackageTable.UUID == uuidx)
        )
        return self.fetch_first(stmt)
