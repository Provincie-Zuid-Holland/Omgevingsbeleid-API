from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class ReferencedGebiedengroepCodeExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        existing_gebiedengroepen: set[str] = {
            gebiedengroep.code for gebiedengroep in request.input_data.Publication_Data.gebiedengroepen.values()
        }

        for used_object in request.input_data.Publication_Data.used_objects:
            gebiedengroep_code: str | None = used_object.get("Gebiedengroep_Code")
            if not gebiedengroep_code:
                continue

            if gebiedengroep_code not in existing_gebiedengroepen:
                errors.append(
                    ValidatePublicationError(
                        rule="referenced_gebiedengroep_code_exists_rule",
                        object=ValidatePublicationObject(
                            code=used_object.get("Code"),
                            object_id=used_object.get("Object_ID"),
                            object_type=used_object.get("Object_Type"),
                            title=used_object.get("Title"),
                        ),
                        messages=[f"Gebiedengroep code '{gebiedengroep_code}' can't be found in publication"],
                    )
                )

        return errors
