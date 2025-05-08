import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.core.tables.publications import PublicationActTable, PublicationActVersionTable


class ActFrbrProvider:
    def __init__(self, db: Session):
        self._db: Session = db

    def generate_frbr(self, act: PublicationActTable) -> ActFrbr:
        expression_version: int = self._get_next_expression_version(act.UUID)

        timepoint: datetime = datetime.now(timezone.utc)
        frbr: ActFrbr = ActFrbr(
            Act_ID=act.ID,
            Work_Province_ID=act.Work_Province_ID,
            Work_Country=act.Work_Country,
            Work_Date=act.Work_Date,
            Work_Other=act.Work_Other,
            Expression_Language=act.Environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=expression_version,
        )
        return frbr

    def _get_next_expression_version(self, act_uuid: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(PublicationActVersionTable)
            .filter(PublicationActVersionTable.Act_UUID == act_uuid)
        )
        next_expression_version: int = self._db.execute(stmt).scalar() + 1
        return next_expression_version
