from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.api.domains.publications.repository import PublicationObjectRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


class RequireExistingHierarchyCodeRuleConfig(BaseModel):
    field: str


class RequireExistingHierarchyCodeRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig, repository: PublicationObjectRepository):
        self._config: RequireExistingHierarchyCodeRuleConfig = main_config.get_as_model(
            "validate_rules.module.require_existing_hierarchy_code",
            RequireExistingHierarchyCodeRuleConfig,
        )
        self._repository: PublicationObjectRepository = repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        objects: list[dict] = self._repository.fetch_objects(
            db,
            request.module_id,
            datetime.now(UTC),
        )
        existing_object_codes: set[str] = {o["code"] for o in objects}

        errors: list[ValidateModuleError] = []

        for object_info in objects:
            target_code = object_info.get(self._config.field)
            if target_code is None:
                continue

            if target_code not in existing_object_codes:
                module_object: ModuleObjectsTable = request.get_module_object(object_info["code"])
                title: str = module_object.title if module_object and module_object.title else ""

                errors.append(
                    ValidateModuleError(
                        rule="require_existing_hierarchy_code_rule",
                        object=ValidateModuleObject(
                            code=object_info["code"],
                            object_id=object_info["object_id"],
                            object_type=object_info["object_type"],
                            title=title,
                        ),
                        messages=[f"Hierarchy code {target_code} does or will not exist in next version"],
                    )
                )
        return errors
