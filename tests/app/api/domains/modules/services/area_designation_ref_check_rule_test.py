from unittest.mock import Mock

from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingType, GebiedsaanwijzingWaarde
from sqlalchemy.orm import Session

from app.api.domains.modules.services import AreaDesignationRefCheckRule
from app.api.domains.modules.services.validate_module_service import (
    AreaDesignationRefCheckRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: AreaDesignationRefCheckRuleConfig = AreaDesignationRefCheckRuleConfig(
        object_type="gebiedsaanwijzing",
        ref_type_field="Ref_Type",
        ref_group_field="Ref_Group",
    )
    config.get_as_model.return_value = rule_config

    def _get_gebiedsaanwijzing(deprecated: bool) -> Mock | Gebiedsaanwijzing:
        aanwijzing_type: Mock | GebiedsaanwijzingType = Mock(GebiedsaanwijzingType)
        aanwijzing_type.deprecated = deprecated
        gebiedsaanwijzing: Mock | Gebiedsaanwijzing = Mock(Gebiedsaanwijzing)
        gebiedsaanwijzing.aanwijzing_type = aanwijzing_type
        return gebiedsaanwijzing

    gebiedsaanwijzing_1 = _get_gebiedsaanwijzing(deprecated=False)
    gebiedsaanwijzing_2 = _get_gebiedsaanwijzing(deprecated=True)

    def fake_get_by_type_label(ref: str) -> Mock | Gebiedsaanwijzing | None:
        return {
            "ref_1": gebiedsaanwijzing_1,
            "ref_2": None,
            "ref_3": gebiedsaanwijzing_2,
        }.get(ref)

    gebiedsaanwijzingen: Mock | Gebiedsaanwijzingen = Mock(Gebiedsaanwijzingen)
    gebiedsaanwijzingen.get_by_type_label.side_effect = fake_get_by_type_label

    waarde_1: Mock | GebiedsaanwijzingWaarde = Mock(GebiedsaanwijzingWaarde)
    waarde_1.deprecated = False
    waarde_2: Mock | GebiedsaanwijzingWaarde = Mock(GebiedsaanwijzingWaarde)
    waarde_2.deprecated = True

    def fake_get_value_by_label(ref_group: str) -> Mock | GebiedsaanwijzingWaarde | None:
        return {
            "ref_group_1": waarde_1,
            "ref_group_2": None,
            "ref_group_3": waarde_2,
        }.get(ref_group)

    gebiedsaanwijzing_1.get_value_by_label.side_effect = fake_get_value_by_label

    factory: GebiedsaanwijzingenFactory = Mock(GebiedsaanwijzingenFactory)
    factory.get_for_document.return_value = gebiedsaanwijzingen
    rule: AreaDesignationRefCheckRule = AreaDesignationRefCheckRule(config, factory)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="beleidsdoel",  # Not a gebiedsaanwijzing
                Object_ID="1",
                Code="beleidsdoel-1",
                Title="BD1 title",
            ),
            ModuleObjectsTable(
                Object_Type="gebiedsaanwijzing",
                Object_ID="1",
                Code="gebiedsaanwijzing-1",
                Title="GA1 title",
                Ref_Type="ref_1",
                Ref_Group="ref_group_1",
            ),
            ModuleObjectsTable(
                Object_Type="gebiedsaanwijzing",
                Object_ID="2",
                Code="gebiedsaanwijzing-2",
                Title="GA2 title",
                Ref_Type="ref_2",  # ref type None
            ),
            ModuleObjectsTable(
                Object_Type="gebiedsaanwijzing",
                Object_ID="3",
                Code="gebiedsaanwijzing-3",
                Title="GA3 title",
                Ref_Type="ref_3",  # ref type deprecated
            ),
            ModuleObjectsTable(
                Object_Type="gebiedsaanwijzing",
                Object_ID="4",
                Code="gebiedsaanwijzing-4",
                Title="GA4 title",
                Ref_Type="ref_1",
                Ref_Group="ref_group_2",  # ref group None
            ),
            ModuleObjectsTable(
                Object_Type="gebiedsaanwijzing",
                Object_ID="5",
                Code="gebiedsaanwijzing-5",
                Title="GA5 title",
                Ref_Type="ref_1",
                Ref_Group="ref_group_3",  # ref group deprecated
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == [
        "gebiedsaanwijzing-2",
        "gebiedsaanwijzing-3",
        "gebiedsaanwijzing-4",
        "gebiedsaanwijzing-5",
    ]
