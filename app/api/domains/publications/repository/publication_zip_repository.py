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
    def get_by_id(self, session: Session, idx: UUID) -> PublicationPackageZipTable | None:
        stmt = select(PublicationPackageZipTable).filter(PublicationPackageZipTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_by_act_package_id(self, session: Session, idx: UUID) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationActPackageTable)
            .filter(PublicationActPackageTable.id == idx)
        )
        return self.fetch_first(session, stmt)

    def get_by_announcement_package_id(self, session: Session, idx: UUID) -> PublicationPackageZipTable | None:
        stmt = (
            select(PublicationPackageZipTable)
            .join(PublicationAnnouncementPackageTable)
            .filter(PublicationAnnouncementPackageTable.id == idx)
        )
        return self.fetch_first(session, stmt)
