from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module_service import (
    ForbiddenHtmlTagsRule,
    ForbiddenHtmlTagsRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: ForbiddenHtmlTagsRuleConfig = ForbiddenHtmlTagsRuleConfig(
        fields=["Description"],
        forbidden_html_tags=["p"],
    )
    config.get_as_model.return_value = rule_config
    rule: ForbiddenHtmlTagsRule = ForbiddenHtmlTagsRule(config)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="1",
                Code="ambitie-1",
                Title="A1 title",
                Description="<p>A1 description</p>",  # has forbidden p tag
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="2",
                Code="ambitie-2",
                Title="A2 title",
                Description="<span>A2 description</span>",  # valid
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="3",
                Code="ambitie-3",
                Title="A3 title",
                Explanation="<p>A3 explanation</p>",  # field is not checked
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["ambitie-1"]
