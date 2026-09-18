from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class UsedObjectInPublicationExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        used_object_types_in_template: set[str] = set()
        for used_object_code in request.input_data.Publication_Data.used_object_codes:
            object_type, _ = used_object_code.split("-")
            used_object_types_in_template.add(object_type)

        for object_current in request.input_data.Publication_Data.all_objects:
            if object_current.get("Object_Type") not in used_object_types_in_template:
                continue

            if object_current.get("Code") not in request.input_data.Publication_Data.used_object_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_object_in_publication_exists_rule",
                        object=ValidatePublicationObject(
                            code=object_current.get("Code"),
                            object_id=object_current.get("Object_ID"),
                            object_type=object_current.get("Object_Type"),
                            title=object_current.get("Title", ""),
                        ),
                        messages=[f"Object {object_current.get('Code')} can't be found in publication"],
                    )
                )
        return errors
