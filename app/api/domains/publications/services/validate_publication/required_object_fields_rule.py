from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class RequiredObjectFieldsRule(ValidatePublicationRule):
    def __init__(self, document_type_map: dict[str, dict[str, type[BaseModel]]]):
        self._document_type_map: dict[str, dict[str, type[BaseModel]]] = document_type_map

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        object_map = self._document_type_map.get(request.document_type)

        for object_to_validate in request.input_data.Publication_Data.used_objects:
            model: type[BaseModel] | None = object_map.get(object_to_validate.get("Object_Type"))
            if not model:
                continue

            try:
                _ = model.model_validate(object_to_validate)
            except ValidationError as e:
                errors.append(
                    ValidatePublicationError(
                        rule="required_object_fields_rule",
                        object=ValidatePublicationObject(
                            code=object_to_validate.get("Code"),
                            object_id=object_to_validate.get("Object_ID"),
                            object_type=object_to_validate.get("Object_Type"),
                            title=object_to_validate.get("Title"),
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors
