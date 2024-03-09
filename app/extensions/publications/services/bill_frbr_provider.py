import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.extensions.publications.enums import PackageType
from app.extensions.publications.tables.tables import (
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)


@dataclass
class BillFrbr:
    Work_Country: str
    Work_Date: str
    Work_Other: str
    Expression_Language: str
    Expression_Date: str
    Expression_Version: str
    Expression_Other: Optional[str]


class BillFrbrProvider:
    def __init__(self):
        pass

    def generate_frbr(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> BillFrbr:
        match (publication_version.Environment.Has_State, package_type):
            case (False, _):
                return self._fake(publication_version)
            case _:
                raise NotImplementedError("Not implemented yet")

    def _predict_offcial(self):
        pass

    def _official(self):
        pass

    def _fake(self, publication_version: PublicationVersionTable):
        publication: PublicationTable = publication_version.Publication
        environment: PublicationEnvironmentTable = publication_version.Environment

        timepoint: datetime = datetime.utcnow()
        frbr: BillFrbr = BillFrbr(
            Work_Country=environment.Frbr_Country,
            Work_Date=str(timepoint.year),
            Work_Other=f"{publication.Document_Type.lower()}-{uuid.uuid4().hex[:8]}",
            Expression_Language=environment.Frbr_Language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version="1",
            Expression_Other=None,
        )
        return frbr
