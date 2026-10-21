from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
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
        fields=["description"],
        forbidden_html_tags=["p"],
    )
    config.get_as_model.return_value = rule_config
    rule: ForbiddenHtmlTagsRule = ForbiddenHtmlTagsRule(config)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="1",
                code="ambitie-1",
                title="A1 title",
                description="<p>A1 description</p>",  # has forbidden p tag
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="2",
                code="ambitie-2",
                title="A2 title",
                description="<span>A2 description</span>",  # valid
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="3",
                code="ambitie-3",
                title="A3 title",
                explanation="<p>A3 explanation</p>",  # field is not checked
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["ambitie-1"]
