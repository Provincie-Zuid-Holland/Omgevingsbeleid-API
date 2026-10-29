import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.types.api_input_data import DocFrbr
from app.core.tables.publications import (
    PublicationActVersionTable,
    PublicationAnnouncementTable,
    PublicationDocTable,
    PublicationEnvironmentTable,
    PublicationTable,
)


class DocFrbrProvider:
    async def generate_frbr(self, session: AsyncSession, announcement: PublicationAnnouncementTable) -> DocFrbr:
        if announcement.publication.environment.has_state:
            return await self._create_real(session, announcement)

        return self._create_fake(announcement)

    async def _create_real(self, session: AsyncSession, announcement: PublicationAnnouncementTable) -> DocFrbr:
        stmt = select(func.count()).select_from(PublicationDocTable)
        count: int = (await session.execute(stmt)).scalar() + 1
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
        act_version: PublicationActVersionTable = announcement.act_package.act_version
        publication: PublicationTable = announcement.publication
        environment: PublicationEnvironmentTable = publication.environment

        work_other: str = f"kennisgeving-{act_version.act.work_other}-{id_suffix}"

        timepoint: datetime = datetime.now(UTC)
        frbr: DocFrbr = DocFrbr(
            work_province_id=environment.province_id,
            work_country=environment.frbr_country,
            work_date=str(timepoint.year),
            work_other=work_other,
            expression_language=environment.frbr_language,
            expression_date=timepoint.strftime("%Y-%m-%d"),
            expression_version=1,
            document_type=publication.document_type,
        )
        return frbr
