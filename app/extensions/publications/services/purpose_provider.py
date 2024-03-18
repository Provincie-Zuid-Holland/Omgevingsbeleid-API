from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from app.extensions.publications.enums import PurposeType
from app.extensions.publications.models.api_input_data import ActFrbr, Purpose
from app.extensions.publications.tables.tables import PublicationEnvironmentTable, PublicationVersionTable

TYPE_MAP: Dict[str, str] = {
    PurposeType.CONSOLIDATION: "instelling",
    PurposeType.WITHDRAWAL: "intrekken",
}


class PurposeProvider:
    def __init__(self, db: Session):
        self._db: Session = db

    def generate_purpose(
        self,
        publication_version: PublicationVersionTable,
        act_frbr: ActFrbr,
        purpose_type: PurposeType,
    ) -> Purpose:
        if publication_version.Environment.Has_State:
            return self._create_real(publication_version, act_frbr, purpose_type)

        return self._create_fake(publication_version, act_frbr, purpose_type)

    def _create_real(
        self,
        publication_version: PublicationVersionTable,
        act_frbr: ActFrbr,
        purpose_type: PurposeType,
    ) -> Purpose:
        # @note: For now we do the same as fake
        result: Purpose = self._create_fake(publication_version, act_frbr, purpose_type)
        return result

    def _create_fake(
        self,
        publication_version: PublicationVersionTable,
        act_frbr: ActFrbr,
        purpose_type: PurposeType,
    ) -> Purpose:
        work_other: str = "-".join(
            [
                TYPE_MAP[purpose_type],
                act_frbr.Work_Other.lower(),
                str(act_frbr.Expression_Version),
            ]
        )
        result: Purpose = self._create(publication_version, purpose_type, work_other)
        return result

    def _create(
        self,
        publication_version: PublicationVersionTable,
        purpose_type: PurposeType,
        work_other: str,
    ) -> Purpose:
        environment: PublicationEnvironmentTable = publication_version.Environment

        timepoint: datetime = datetime.utcnow()
        purpose: Purpose = Purpose(
            Purpose_Type=purpose_type,
            Effective_Date=publication_version.Effective_Date,
            Work_Province_ID=environment.Province_ID,
            Work_Date=str(timepoint.year),
            Work_Other=work_other,
        )
        return purpose
