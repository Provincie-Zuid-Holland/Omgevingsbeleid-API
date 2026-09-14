from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services import ForbidEmptyHtmlNodesRule
from app.api.domains.modules.services.validate_module_service import (
    ForbidEmptyHtmlNodesRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: ForbidEmptyHtmlNodesRuleConfig = ForbidEmptyHtmlNodesRuleConfig(
        fields=["Description"], html_void_elements=["img"], allowed_empty_when_sole_child={"td": ["p"]}
    )
    config.get_as_model.return_value = rule_config
    rule: ForbidEmptyHtmlNodesRule = ForbidEmptyHtmlNodesRule(config)

    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="1",
                Code="ambitie-1",
                Title="A1 title",
                Description="<p></p>",  # has forbidden void tag
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="2",
                Code="ambitie-2",
                Title="A2 title",
                Description="<img />",  # has allowed void tag
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="3",
                Code="ambitie-3",
                Title="A3 title",
                Description="<td><p></p></td>",  # has allowed void tag, when sole child
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="4",
                Code="ambitie-4",
                Title="A4 title",
                Description="<td><p></p><p>content</p></td>",  # has not allowed void tag, because is not sole child
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="5",
                Code="ambitie-5",
                Title="A5 title",
                Description="<td><p>content</p><p></p></td>",  # has not allowed void tag, because is not sole child
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="6",
                Code="ambitie-6",
                Title="A6 title",
                Description="<div><p></p></div>",  # has not allowed void tag, because is sole child in unknown parent tag
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == ["ambitie-1", "ambitie-4", "ambitie-5", "ambitie-6"]
