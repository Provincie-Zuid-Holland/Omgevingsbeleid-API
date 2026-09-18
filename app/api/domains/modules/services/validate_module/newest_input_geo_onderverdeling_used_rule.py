from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
    ValidateModuleSeverity,
)
from app.api.domains.werkingsgebieden.repositories import InputGeoOnderverdelingRepository
from app.core.services import MainConfig
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


class NewestInputGeoOnderverdelingUsedRuleConfig(BaseModel):
    object_type: str
    field: str


class NewestInputGeoOnderverdelingUsedRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig, repository: InputGeoOnderverdelingRepository):
        self._config: NewestInputGeoOnderverdelingUsedRuleConfig = main_config.get_as_model(
            "validate_rules.module.newest_input_geo_onderverdeling_used",
            NewestInputGeoOnderverdelingUsedRuleConfig,
        )
        self._input_geo_onderverdeling_repository: InputGeoOnderverdelingRepository = repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            if object_table.Object_Type != self._config.object_type:
                continue

            area_current: AreasTable | None = getattr(object_table, self._config.field)
            if area_current is None:
                errors.append(
                    ValidateModuleError(
                        rule="newest_input_geo_onderverdeling_used_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[f"Object is of type '{self._config.object_type}', but area is not known"],
                    )
                )
                continue

            area_hash: str = area_current.source_geometry_hash or ""
            area_title: str = area_current.source_title
            onderverdeling: InputGeoOnderverdelingenTable | None = (
                self._input_geo_onderverdeling_repository.get_latest_by_title(db, area_title)
            )
            if onderverdeling is None:
                errors.append(
                    ValidateModuleError(
                        rule="newest_input_geo_onderverdeling_used_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"The onderverdelingen lineage used by Area `{area_current.id}` with source title `{area_title}` can no longer be found in InputGeoOnderverdelingen"
                        ],
                        severity=ValidateModuleSeverity.warning,
                    )
                )
                continue

            if area_hash != onderverdeling.Geometry_Hash:
                errors.append(
                    ValidateModuleError(
                        rule="newest_input_geo_onderverdeling_used_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"Area {area_current.id} does not use the latest known onderverdeling shape {onderverdeling.UUID}"
                        ],
                        severity=ValidateModuleSeverity.warning,
                    )
                )
                continue

        return errors
