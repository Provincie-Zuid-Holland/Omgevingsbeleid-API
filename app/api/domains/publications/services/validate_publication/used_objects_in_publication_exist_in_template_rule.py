from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class UsedObjectsInPublicationExistInTemplateRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        publication_data_codes = [
            object_to_validate.get("code") for object_to_validate in request.input_data.Publication_Data.used_objects
        ]
        for used_code_in_template in request.input_data.Publication_Data.used_object_codes:
            if used_code_in_template not in publication_data_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_objects_in_publication_exist_in_template_rule",
                        object=ValidatePublicationObject(),  # there is no actual object to show in the error
                        messages=[
                            f"Object with code '{used_code_in_template}' used in template can't be found in publication"
                        ],
                    )
                )
        return errors
