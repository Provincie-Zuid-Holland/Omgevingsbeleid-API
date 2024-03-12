import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.extensions.publications.enums import PackageType
from app.extensions.publications.tables.tables import (
    PublicationBillTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)


@dataclass
class BillFrbr:
    Document_Type: str
    Work_Country: str
    Work_Date: str
    Work_Other: str
    Expression_Language: str
    Expression_Date: str
    Expression_Version: int
    Expression_Other: Optional[str]


class BillFrbrProvider:
    def __init__(self, db: Session):
        self._db: Session = db

    def generate_frbr(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> BillFrbr:
        if publication_version.Environment.Has_State:
            return self._create_real(publication_version, package_type)

        return self._create_fake(publication_version, package_type)

    def _create_real(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> BillFrbr:
        stmt = (
            select(func.count())
            .select_from(PublicationBillTable)
            .filter(PublicationBillTable.Document_Type == publication_version.Publication.Document_Type)
        )
        count: int = self._db.execute(stmt).scalar() + 1
        id_suffix: str = f"{count}"
        result: BillFrbr = self._create(publication_version, package_type, id_suffix)
        return result

    def _create_fake(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> BillFrbr:
        id_suffix: str = uuid.uuid4().hex[:8]
        result: BillFrbr = self._create(publication_version, package_type, id_suffix)
        return result

    def _create(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
        id_suffix: str,
    ) -> BillFrbr:
        publication: PublicationTable = publication_version.Publication
        environment: PublicationEnvironmentTable = publication_version.Environment

        timepoint: datetime = datetime.utcnow()
        frbr: BillFrbr = BillFrbr(
            Work_Country=environment.Frbr_Country,
            Work_Date=str(timepoint.year),
            Work_Other=f"{publication.Document_Type.lower()}-{id_suffix}",
            Expression_Language=environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=1,
            Expression_Other=None,
            Document_Type=publication.Document_Type,
        )
        return frbr
