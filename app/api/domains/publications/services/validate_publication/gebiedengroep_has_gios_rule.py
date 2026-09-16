from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class GebiedengroepHasGiosRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        for gebiedengroep in request.input_data.Publication_Data.gebiedengroepen.values():
            if not gebiedengroep.gio_key:
                errors.append(
                    ValidatePublicationError(
                        rule="gebiedengroep_has_no_gio",
                        object=ValidatePublicationObject(
                            code=gebiedengroep.code,
                            title=gebiedengroep.title,
                        ),
                        messages=[f"Gebiedengroep code '{gebiedengroep.code}' has no valid gio"],
                    )
                )

        return errors
