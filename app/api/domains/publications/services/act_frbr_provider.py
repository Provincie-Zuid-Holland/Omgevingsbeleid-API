import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.core.tables.publications import PublicationActTable, PublicationActVersionTable


class ActFrbrProvider:
    def generate_frbr(self, session: Session, act: PublicationActTable) -> ActFrbr:
        expression_version: int = self._get_next_expression_version(session, act.uuid)

        timepoint: datetime = datetime.now(UTC)
        frbr: ActFrbr = ActFrbr(
            Act_ID=act.id,
            Work_Province_ID=act.work_province_id,
            Work_Country=act.work_country,
            Work_Date=act.work_date,
            Work_Other=act.work_other,
            Expression_Language=act.environment.frbr_language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=expression_version,
        )
        return frbr

    def _get_next_expression_version(self, session: Session, act_uuid: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(PublicationActVersionTable)
            .filter(PublicationActVersionTable.act_id == act_uuid)
        )
        next_expression_version: int = session.execute(stmt).scalar() + 1
        return next_expression_version
