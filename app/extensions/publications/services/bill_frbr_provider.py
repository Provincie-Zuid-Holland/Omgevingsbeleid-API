import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.extensions.publications.models import BillFrbr
from app.extensions.publications.models.api_input_data import ActFrbr
from app.extensions.publications.tables.tables import PublicationBillTable, PublicationEnvironmentTable


class BillFrbrProvider:
    def __init__(self, db: Session):
        self._db: Session = db

    def generate_frbr(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        if environment.Has_State:
            return self._create_real(environment, act_frbr)

        return self._create_fake(environment, act_frbr)

    def _create_real(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        stmt = select(func.count()).select_from(PublicationBillTable)
        count: int = (self._db.execute(stmt).scalar()) + 1
        id_suffix: str = f"{count}"
        result: BillFrbr = self._create(environment, act_frbr, id_suffix)
        return result

    def _create_fake(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        id_suffix: str = uuid.uuid4().hex[:8]
        result: BillFrbr = self._create(environment, act_frbr, id_suffix)
        return result

    def _create(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
        id_suffix: str,
    ) -> BillFrbr:
        work_other: str = f"{act_frbr.Work_Other}-{id_suffix}"

        timepoint: datetime = datetime.now(timezone.utc)
        frbr: BillFrbr = BillFrbr(
            Work_Province_ID=environment.Province_ID,
            Work_Country=environment.Frbr_Country,
            Work_Date=str(timepoint.year),
            Work_Other=work_other,
            Expression_Language=environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=1,
        )
        return frbr
