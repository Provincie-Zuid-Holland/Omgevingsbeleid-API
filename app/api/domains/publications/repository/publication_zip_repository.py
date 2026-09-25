from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationPackageZipTable,
)


class PublicationZipRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: UUID) -> PublicationPackageZipTable | None:
        stmt = select(PublicationPackageZipTable).filter(PublicationPackageZipTable.id == uuidx)
        return self.fetch_first(session, stmt)

    def get_by_act_package_uuid(self, session: Session, uuidx: UUID) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationActPackageTable)
            .filter(PublicationActPackageTable.id == uuidx)
        )
        return self.fetch_first(session, stmt)

    def get_by_announcement_package_uuid(self, session: Session, uuidx: UUID) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationAnnouncementPackageTable)
            .filter(PublicationAnnouncementPackageTable.id == uuidx)
        )
        return self.fetch_first(session, stmt)
