from unittest.mock import Mock

from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    AreaDesignationRefCheckRule,
    AreaDesignationRefCheckRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable
from tests.dso.factories.gebiedsaanwijzing import make_gebiedsaanwijzing


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: AreaDesignationRefCheckRuleConfig = AreaDesignationRefCheckRuleConfig(
        object_type="gebiedsaanwijzing",
        ref_type_field="ref_type",
        ref_group_field="ref_group",
    )
    config.get_as_model.return_value = rule_config

    gebiedsaanwijzing_1 = make_gebiedsaanwijzing(deprecated=False)
    gebiedsaanwijzing_2 = make_gebiedsaanwijzing(deprecated=True)

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
                object_type="beleidsdoel",  # Not a gebiedsaanwijzing
                object_id="1",
                code="beleidsdoel-1",
                title="BD1 title",
            ),
            ModuleObjectsTable(
                object_type="gebiedsaanwijzing",
                object_id="1",
                code="gebiedsaanwijzing-1",
                title="GA1 title",
                ref_type="ref_1",
                ref_group="ref_group_1",
            ),
            ModuleObjectsTable(
                object_type="gebiedsaanwijzing",
                object_id="2",
                code="gebiedsaanwijzing-2",
                title="GA2 title",
                ref_type="ref_2",  # ref type None
            ),
            ModuleObjectsTable(
                object_type="gebiedsaanwijzing",
                object_id="3",
                code="gebiedsaanwijzing-3",
                title="GA3 title",
                ref_type="ref_3",  # ref type deprecated
            ),
            ModuleObjectsTable(
                object_type="gebiedsaanwijzing",
                object_id="4",
                code="gebiedsaanwijzing-4",
                title="GA4 title",
                ref_type="ref_1",
                ref_group="ref_group_2",  # ref group None
            ),
            ModuleObjectsTable(
                object_type="gebiedsaanwijzing",
                object_id="5",
                code="gebiedsaanwijzing-5",
                title="GA5 title",
                ref_type="ref_1",
                ref_group="ref_group_3",  # ref group deprecated
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
