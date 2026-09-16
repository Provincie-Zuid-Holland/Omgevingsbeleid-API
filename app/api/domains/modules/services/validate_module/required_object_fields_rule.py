from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)


class RequiredObjectFieldsRule(ValidateModuleRule):
    def __init__(self, object_map: dict[str, type[BaseModel]]):
        self._object_map: dict[str, type[BaseModel]] = object_map

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for module_object_table in request.module_objects:
            model: type[BaseModel] | None = self._object_map.get(module_object_table.Object_Type)
            if not model:
                continue

            try:
                _ = model.model_validate(module_object_table)
            except ValidationError as e:
                errors.append(
                    ValidateModuleError(
                        rule="required_object_fields_rule",
                        object=ValidateModuleObject(
                            code=module_object_table.Code,
                            object_id=module_object_table.Object_ID,
                            object_type=module_object_table.Object_Type,
                            title=module_object_table.Title,
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors
