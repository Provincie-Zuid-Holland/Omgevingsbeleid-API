from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
    ValidateModuleSeverity,
)
from app.core.services import MainConfig


class CheckEmptyAreaDesignationTextConfig(BaseModel):
    fields: list[str]


class CheckEmptyAreaDesignationTextRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: CheckEmptyAreaDesignationTextConfig = main_config.get_as_model(
            "validate_rules.module.check_empty_area_designation_text",
            CheckEmptyAreaDesignationTextConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                soup = BeautifulSoup(value, "html.parser")
                for gebiedsaanwijzing in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
                    inner_text = gebiedsaanwijzing.get_text(strip=True)
                    if len(inner_text) == 0:
                        errors.append(
                            ValidateModuleError(
                                rule="check_empty_area_designation_text_rule",
                                object=ValidateModuleObject(
                                    code=object_table.code,
                                    object_id=object_table.object_id,
                                    object_type=object_table.object_type,
                                    title=object_table.title,
                                ),
                                severity=ValidateModuleSeverity.warning,
                                messages=[
                                    f"Gebiedsaanwijzing '{gebiedsaanwijzing.get('data-code', '')}' in '{field_name}' has no selected text"
                                ],
                            )
                        )
        return errors
