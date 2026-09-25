import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.publications import PublicationActTable, PublicationActVersionTable


class PublicationActVersionRepository(BaseRepository):
    def get_by_work_expression(
        self,
        session: Session,
        environment_uuid: uuid.UUID,
        document_type: str,
        procedure_type: str,
        work_province_id: str,
        work_country: str,
        work_date: str,
        work_other: str,
        expression_language: str,
        expression_date: str,
        expression_version: int,
    ) -> PublicationActVersionTable | None:
        stmt = (
            select(PublicationActVersionTable)
            .join(PublicationActTable)
            .filter(PublicationActTable.environment_id == environment_uuid)
            .filter(PublicationActTable.document_type == document_type)
            .filter(PublicationActTable.procedure_type == procedure_type)
            .filter(PublicationActTable.work_province_id == work_province_id)
            .filter(PublicationActTable.work_country == work_country)
            .filter(PublicationActTable.work_date == work_date)
            .filter(PublicationActTable.work_other == work_other)
            .filter(PublicationActVersionTable.expression_language == expression_language)
            .filter(PublicationActVersionTable.expression_date == expression_date)
            .filter(PublicationActVersionTable.expression_version == expression_version)
        )

        result: PublicationActVersionTable | None = self.fetch_first(session, stmt)
        return result
