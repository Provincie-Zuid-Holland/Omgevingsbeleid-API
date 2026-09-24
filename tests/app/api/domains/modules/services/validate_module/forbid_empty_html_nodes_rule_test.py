from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    ForbidEmptyHtmlNodesRule,
    ForbidEmptyHtmlNodesRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: ForbidEmptyHtmlNodesRuleConfig = ForbidEmptyHtmlNodesRuleConfig(
        fields=["description"], html_void_elements=["img"], allowed_empty_when_sole_child={"td": ["p"]}
    )
    config.get_as_model.return_value = rule_config
    rule: ForbidEmptyHtmlNodesRule = ForbidEmptyHtmlNodesRule(config)

    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="1",
                code="ambitie-1",
                title="A1 title",
                description="<p></p>",  # has forbidden void tag
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="2",
                code="ambitie-2",
                title="A2 title",
                description="<img />",  # has allowed void tag
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="3",
                code="ambitie-3",
                title="A3 title",
                description="<td><p></p></td>",  # has allowed void tag, when sole child
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="4",
                code="ambitie-4",
                title="A4 title",
                description="<td><p></p><p>content</p></td>",  # has not allowed void tag, because is not sole child
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="5",
                code="ambitie-5",
                title="A5 title",
                description="<td><p>content</p><p></p></td>",  # has not allowed void tag, because is not sole child
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="6",
                code="ambitie-6",
                title="A6 title",
                description="<div><p></p></div>",  # has not allowed void tag, because is sole child in unknown parent tag
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == ["ambitie-1", "ambitie-4", "ambitie-5", "ambitie-6"]
