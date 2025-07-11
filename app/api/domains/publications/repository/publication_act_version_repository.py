import uuid
from typing import Optional

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
    ) -> Optional[PublicationActVersionTable]:
        stmt = (
            select(PublicationActVersionTable)
            .join(PublicationActTable)
            .filter(PublicationActTable.Environment_UUID == environment_uuid)
            .filter(PublicationActTable.Document_Type == document_type)
            .filter(PublicationActTable.Procedure_Type == procedure_type)
            .filter(PublicationActTable.Work_Province_ID == work_province_id)
            .filter(PublicationActTable.Work_Country == work_country)
            .filter(PublicationActTable.Work_Date == work_date)
            .filter(PublicationActTable.Work_Other == work_other)
            .filter(PublicationActVersionTable.Expression_Language == expression_language)
            .filter(PublicationActVersionTable.Expression_Date == expression_date)
            .filter(PublicationActVersionTable.Expression_Version == expression_version)
        )

        result: Optional[PublicationActVersionTable] = self.fetch_first(session, stmt)
        return result
