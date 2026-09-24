from dso.services.koop.waardelijsten.gen import OnderwerpType, RechtsgebiedType
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class WaardelijstenValuesUsedCheckRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        koop_subjects: list[str] = [subject for subject in OnderwerpType.__members__]
        for subject in request.input_data.Publication_Version.Bill_Metadata["Subjects"]:
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
        for jurisdiction in request.input_data.Publication_Version.Bill_Metadata["Jurisdictions"]:
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
