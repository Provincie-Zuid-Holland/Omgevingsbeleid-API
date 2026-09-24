from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    RequireExistingHierarchyCodeRule,
    RequireExistingHierarchyCodeRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.api.domains.publications.repository import PublicationObjectRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: RequireExistingHierarchyCodeRuleConfig = RequireExistingHierarchyCodeRuleConfig(field="hierarchy_code")
    config.get_as_model.return_value = rule_config
    repository: Mock | PublicationObjectRepository = Mock(PublicationObjectRepository)
    repository.fetch_objects.return_value = [
        {
            "code": "ambitie-1",
            "hierarchy_code": "beleidsdoel-1",  # connects to existing object
            "object_id": 1,
            "object_type": "ambitie",
        },
        {
            "code": "beleidsdoel-1",
            "hierarchy_code": "beleidskeuze-1",  # connects to non-existing object
            "object_id": 1,
            "object_type": "beleidsdoel",
        },
        {
            "code": "ambitie-2",  # no hierarchy code
            "object_id": 2,
            "object_type": "ambitie",
        },
    ]
    rule: RequireExistingHierarchyCodeRule = RequireExistingHierarchyCodeRule(config, repository)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="beleidsdoel",
                object_id="1",
                code="beleidsdoel-1",
                title="BD1 title",
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["beleidsdoel-1"]
    assert [error.object.title for error in errors] == ["BD1 title"]
