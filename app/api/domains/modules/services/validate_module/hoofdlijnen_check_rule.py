from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


@dataclass
class HoofdlijnenCheckRuleData:
    hoofdlijnen_ids: set[UUID]
    object_table: ModuleObjectsTable


class HoofdlijnenCheckRuleConfig(BaseModel):
    field: str
    allowed_object_types: list[str]


class HoofdlijnenCheckRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig, hoofdlijn_repository: HoofdlijnRepository):
        self._config: HoofdlijnenCheckRuleConfig = main_config.get_as_model(
            "validate_rules.module.hoofdlijnen_check",
            HoofdlijnenCheckRuleConfig,
        )
        self._hoofdlijn_repository: HoofdlijnRepository = hoofdlijn_repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        object_data: list[HoofdlijnenCheckRuleData] = []
        hoofdlijnen_set: set[UUID] = set()

        errors: list[ValidateModuleError] = []
        for object_table in request.module_objects:
            if object_table.object_type not in self._config.allowed_object_types:
                continue

            field_value: list[str] | None = getattr(object_table, self._config.field)
            if not field_value:
                continue

            hoofdlijnen_ids: set[UUID] = {UUID(hoofdlijn_id) for hoofdlijn_id in field_value}
            object_data.append(HoofdlijnenCheckRuleData(hoofdlijnen_ids=hoofdlijnen_ids, object_table=object_table))
            hoofdlijnen_set.update(hoofdlijnen_ids)

        if not hoofdlijnen_set:
            return errors

        found_hoofdlijnen_ids: set[UUID] = self._hoofdlijn_repository.get_existing_ids(db, hoofdlijnen_set)
        missing_ids = hoofdlijnen_set - found_hoofdlijnen_ids
        if not missing_ids:
            return errors

        for data in object_data:
            missing_for_object: set[UUID] = data.hoofdlijnen_ids & missing_ids
            if missing_for_object:
                missing_displayed: list[str] = sorted(str(idx) for idx in missing_for_object)
                errors.append(
                    ValidateModuleError(
                        rule="hoofdlijnen_check_rule",
                        object=ValidateModuleObject(
                            code=data.object_table.code,
                            object_id=data.object_table.object_id,
                            object_type=data.object_table.object_type,
                            title=data.object_table.title,
                        ),
                        messages=[f"Hoofdlijnen with IDs {', '.join(missing_displayed)} are unknown"],
                    )
                )
        return errors
