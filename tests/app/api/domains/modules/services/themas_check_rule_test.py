from unittest.mock import Mock

from dso import Thema, ThemaFactory
from sqlalchemy.orm import Session

from app.api.domains.modules.services import ThemasCheckRule
from app.api.domains.modules.services.validate_module_service import (
    ThemasCheckRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: ThemasCheckRuleConfig = ThemasCheckRuleConfig(field="Themas")
    config.get_as_model.return_value = rule_config

    def _get_thema(label: str, deprecated: bool) -> Thema:
        return Thema(
            label=label,
            deprecated=deprecated,
            term="term",
            uri="http://some-uri",
            definitie="definitie",
            toelichting="toelichting",
            bron="bron",
            domein="domein",
        )

    factory: Mock | ThemaFactory = Mock(ThemaFactory)
    factory.get_all.return_value = {
        "thema-1": _get_thema(label="thema-1", deprecated=False),
        "thema-2": _get_thema(label="thema-2", deprecated=True),
        "thema-3": _get_thema(label="thema-2", deprecated=False),
    }

    rule: ThemasCheckRule = ThemasCheckRule(config, factory)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="ambitie",  # No themas
                Object_ID="1",
                Code="ambitie-1",
                Title="A1 title",
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="2",
                Code="ambitie-2",
                Title="A2 title",
                Themas=["thema-1"],
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="3",
                Code="ambitie-3",
                Title="A3 title",
                Themas=["thema-2"],  # deprecated
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="4",
                Code="ambitie-4",
                Title="A4 title",
                Themas=["thema-unknown"],  # non-existing
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="5",
                Code="ambitie-5",
                Title="A5 title",
                Themas=["thema-1", "thema-2"],  # one valid, one deprecated
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="6",
                Code="ambitie-6",
                Title="A6 title",
                Themas=["thema-1", "thema-unknown"],  # one valid, one non-existing
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="7",
                Code="ambitie-7",
                Title="A7 title",
                Themas=["thema-1", "thema-3"],  # multiple valid
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == ["ambitie-3", "ambitie-4", "ambitie-5", "ambitie-6"]
