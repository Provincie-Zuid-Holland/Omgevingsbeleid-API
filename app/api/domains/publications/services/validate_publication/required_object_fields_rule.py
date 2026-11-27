from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.api.services.async_model_validators_service import AsyncModelValidatorsService


class RequiredObjectFieldsRule(ValidatePublicationRule):
    def __init__(
        self,
        document_type_map: dict[str, dict[str, type[BaseModel]]],
        async_model_validators_service: AsyncModelValidatorsService,
    ):
        self._document_type_map: dict[str, dict[str, type[BaseModel]]] = document_type_map
        self._async_model_validators_service: AsyncModelValidatorsService = async_model_validators_service

    async def validate(self, db: AsyncSession, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        object_map = self._document_type_map.get(request.document_type)

        for object_to_validate in request.input_data.publication_data.used_objects:
            model: type[BaseModel] | None = object_map.get(object_to_validate.get("object_type"))
            if not model:
                continue

            field_errors: list[ErrorDetails] = []
            try:
                validated: BaseModel = model.model_validate(object_to_validate)
                field_errors = await self._async_model_validators_service.run(db, model, validated, {})
            except ValidationError as e:
                field_errors = e.errors()

            if field_errors:
                errors.append(
                    ValidatePublicationError(
                        rule="required_object_fields_rule",
                        object=ValidatePublicationObject(
                            code=object_to_validate.get("code"),
                            object_id=object_to_validate.get("object_id"),
                            object_type=object_to_validate.get("object_type"),
                            title=object_to_validate.get("title"),
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in field_errors],
                    )
                )
        return errors
