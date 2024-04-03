import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.extensions.publications.enums import ProcedureType
from app.extensions.publications.models import BillFrbr
from app.extensions.publications.tables.tables import (
    PublicationBillTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)


class BillFrbrProvider:
    def __init__(self, db: Session):
        self._db: Session = db

    def generate_frbr(
        self,
        publication_version: PublicationVersionTable,
    ) -> BillFrbr:
        if publication_version.Publication.Environment.Has_State:
            return self._create_real(publication_version)

        return self._create_fake(publication_version)

    def _create_real(
        self,
        publication_version: PublicationVersionTable,
    ) -> BillFrbr:
        stmt = (
            select(func.count())
            .select_from(PublicationBillTable)
            .filter(PublicationBillTable.Document_Type == publication_version.Publication.Document_Type)
            .filter(PublicationBillTable.Environment_UUID == publication_version.Publication.Environment_UUID)
        )
        count: int = self._db.execute(stmt).scalar() + 1
        id_suffix: str = f"{count}"
        result: BillFrbr = self._create(publication_version, id_suffix)
        return result

    def _create_fake(
        self,
        publication_version: PublicationVersionTable,
    ) -> BillFrbr:
        id_suffix: str = uuid.uuid4().hex[:8]
        result: BillFrbr = self._create(publication_version, id_suffix)
        return result

    def _create(
        self,
        publication_version: PublicationVersionTable,
        id_suffix: str,
    ) -> BillFrbr:
        publication: PublicationTable = publication_version.Publication
        environment: PublicationEnvironmentTable = publication.Environment

        draft_prefix: str = ""
        if publication_version.Publication.Procedure_Type == ProcedureType.DRAFT:
            draft_prefix = "ontwerp-"

        timepoint: datetime = datetime.utcnow()
        frbr: BillFrbr = BillFrbr(
            Work_Province_ID=environment.Province_ID,
            Work_Country=environment.Frbr_Country,
            Work_Date=str(timepoint.year),
            Work_Other=f"{draft_prefix}{publication.Document_Type.lower()}-{id_suffix}",
            Expression_Language=environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=1,
        )
        return frbr
