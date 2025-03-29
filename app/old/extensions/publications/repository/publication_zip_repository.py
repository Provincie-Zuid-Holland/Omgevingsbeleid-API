from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.dynamic.repository.repository import BaseRepository
from app.extensions.publications.tables.tables import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationPackageZipTable,
)


class PublicationZipRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[PublicationPackageZipTable]:
        stmt = select(PublicationPackageZipTable).filter(PublicationPackageZipTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_act_package_uuid(self, uuidx: UUID) -> Optional[PublicationPackageZipTable]:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationActPackageTable)
            .filter(PublicationActPackageTable.UUID == uuidx)
        )
        return self.fetch_first(stmt)

    def get_by_announcement_package_uuid(self, uuidx: UUID) -> Optional[PublicationPackageZipTable]:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationAnnouncementPackageTable)
            .filter(PublicationAnnouncementPackageTable.UUID == uuidx)
        )
        return self.fetch_first(stmt)
