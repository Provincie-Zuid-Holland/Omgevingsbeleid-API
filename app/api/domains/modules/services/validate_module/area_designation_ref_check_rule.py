from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
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


class AreaDesignationRefCheckRuleConfig(BaseModel):
    object_type: str
    ref_type_field: str
    ref_group_field: str


class AreaDesignationRefCheckRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig, dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory):
        self._config: AreaDesignationRefCheckRuleConfig = main_config.get_as_model(
            "validate_rules.module.area_designation_ref_check",
            AreaDesignationRefCheckRuleConfig,
        )
        self._dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory = dso_gebiedsaanwijzingen_factory

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []
        gebiedsaanwijzingen: Gebiedsaanwijzingen | None = self._dso_gebiedsaanwijzingen_factory.get_for_document(
            DocumentType.OMGEVINGSVISIE
        )

        for object_table in request.module_objects:
            if object_table.Object_Type != self._config.object_type:
                continue

            ref_type: Gebiedsaanwijzing | None = gebiedsaanwijzingen.get_by_type_label(
                getattr(object_table, self._config.ref_type_field)
            )
            if ref_type is None:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{getattr(object_table, self._config.ref_type_field)}' for gebiedsaanwijzing not found"
                        ],
                    )
                )
                continue
            if ref_type.aanwijzing_type.deprecated:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{getattr(object_table, self._config.ref_type_field)}' for gebiedsaanwijzing is deprecated"
                        ],
                    )
                )
                continue

            ref_group: GebiedsaanwijzingWaarde | None = ref_type.get_value_by_label(
                getattr(object_table, self._config.ref_group_field)
            )
            if ref_group is None:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingGroep '{getattr(object_table, self._config.ref_group_field)}' for GebiedsaanwijzingType '{getattr(object_table, self._config.ref_type_field)}' not found"
                        ],
                    )
                )
                continue
            if ref_group.deprecated:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        severity=ValidateModuleSeverity.warning,
                        messages=[
                            f"GebiedsaanwijzingGroep '{getattr(object_table, self._config.ref_group_field)}' for GebiedsaanwijzingType '{getattr(object_table, self._config.ref_type_field)}' is deprecated"
                        ],
                    )
                )
        return errors
