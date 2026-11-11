from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.api.services.async_model_validators_service import AsyncModelValidatorsService


class RequiredObjectFieldsRule(ValidateModuleRule):
    def __init__(
        self, object_map: dict[str, type[BaseModel]], async_model_validators_service: AsyncModelValidatorsService
    ):
        self._object_map: dict[str, type[BaseModel]] = object_map
        self._async_model_validators_service: AsyncModelValidatorsService = async_model_validators_service

    async def validate(self, db: AsyncSession, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for module_object_table in request.module_objects:
            model: type[BaseModel] | None = self._object_map.get(module_object_table.object_type)
            if not model:
                continue

            field_errors: list[ErrorDetails] = []
            try:
                validated: BaseModel = model.model_validate(module_object_table)
                field_errors = await self._async_model_validators_service.run(db, model, validated, {})
            except ValidationError as e:
                field_errors = e.errors()

            if field_errors:
                errors.append(
                    ValidateModuleError(
                        rule="required_object_fields_rule",
                        object=ValidateModuleObject(
                            code=module_object_table.code,
                            object_id=module_object_table.object_id,
                            object_type=module_object_table.object_type,
                            title=module_object_table.title or "",
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in field_errors],
                    )
                )
        return errors
