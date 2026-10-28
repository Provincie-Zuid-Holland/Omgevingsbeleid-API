from datetime import UTC, datetime

from app.api.domains.publications.types.api_input_data import ActFrbr, Purpose
from app.api.domains.publications.types.enums import PurposeType
from app.core.tables.publications import PublicationEnvironmentTable, PublicationVersionTable

TYPE_MAP: dict[str, str] = {
    PurposeType.CONSOLIDATION: "instelling",
    PurposeType.WITHDRAWAL: "intrekken",
}


class PurposeProvider:
    def generate_purpose(
        self,
        publication_version: PublicationVersionTable,
        act_frbr: ActFrbr,
        purpose_type: PurposeType,
    ) -> Purpose:
        if publication_version.publication.environment.has_state:
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
                act_frbr.work_other.lower(),
                str(act_frbr.expression_version),
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
        environment: PublicationEnvironmentTable = publication_version.publication.environment

        timepoint: datetime = datetime.now(UTC)
        purpose: Purpose = Purpose(
            purpose_type=purpose_type,
            effective_date=publication_version.effective_date,
            work_province_id=environment.province_id,
            work_date=str(timepoint.year),
            work_other=work_other,
        )
        return purpose
