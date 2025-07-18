import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import DocFrbr
from app.core.tables.publications import (
    PublicationActVersionTable,
    PublicationAnnouncementTable,
    PublicationDocTable,
    PublicationEnvironmentTable,
    PublicationTable,
)


class DocFrbrProvider:
    def generate_frbr(self, session: Session, announcement: PublicationAnnouncementTable) -> DocFrbr:
        if announcement.Publication.Environment.Has_State:
            return self._create_real(session, announcement)

        return self._create_fake(announcement)

    def _create_real(self, session: Session, announcement: PublicationAnnouncementTable) -> DocFrbr:
        stmt = select(func.count()).select_from(PublicationDocTable)
        count: int = session.execute(stmt).scalar() + 1
        id_suffix: str = f"{count}"
        result: DocFrbr = self._create(announcement, id_suffix)
        return result

    def _create_fake(self, announcement: PublicationAnnouncementTable) -> DocFrbr:
        id_suffix: str = uuid.uuid4().hex[:8]
        result: DocFrbr = self._create(announcement, id_suffix)
        return result

    def _create(
        self,
        announcement: PublicationAnnouncementTable,
        id_suffix: str,
    ) -> DocFrbr:
        act_version: PublicationActVersionTable = announcement.Act_Package.Act_Version
        publication: PublicationTable = announcement.Publication
        environment: PublicationEnvironmentTable = publication.Environment

        work_other: str = f"kennisgeving-{act_version.Act.Work_Other}-{id_suffix}"

        timepoint: datetime = datetime.now(timezone.utc)
        frbr: DocFrbr = DocFrbr(
            Work_Province_ID=environment.Province_ID,
            Work_Country=environment.Frbr_Country,
            Work_Date=str(timepoint.year),
            Work_Other=work_other,
            Expression_Language=environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=1,
            Document_Type=publication.Document_Type,
        )
        return frbr
