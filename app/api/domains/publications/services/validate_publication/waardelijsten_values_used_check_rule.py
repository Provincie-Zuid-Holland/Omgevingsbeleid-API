from dso.services.koop.waardelijsten.gen import OnderwerpType, RechtsgebiedType
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class WaardelijstenValuesUsedCheckRule(ValidatePublicationRule):
    async def validate(self, db: AsyncSession, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        koop_subjects: list[str] = [subject for subject in OnderwerpType.__members__]
        for subject in request.input_data.Publication_Version.bill_metadata["subjects"]:
            if subject not in koop_subjects:
                errors.append(
                    ValidatePublicationError(
                        rule="waardelijsten_values_used_check_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Subject '{subject}' is not known in waardelijst 'OnderwerpType'",
                        ],
                    )
                )

        koop_jurisdictions: list[str] = [subject for subject in RechtsgebiedType.__members__]
        for jurisdiction in request.input_data.Publication_Version.bill_metadata["jurisdictions"]:
            if jurisdiction not in koop_jurisdictions:
                errors.append(
                    ValidatePublicationError(
                        rule="waardelijsten_values_used_check_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Rechtsgebied '{jurisdiction}' is not known in waardelijst 'RechtsgebiedType'",
                        ],
                    )
                )
        return errors
