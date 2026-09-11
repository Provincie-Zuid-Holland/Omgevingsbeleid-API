from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services import RequireExistingHierarchyCodeRule
from app.api.domains.modules.services.validate_module_service import (
    RequireExistingHierarchyCodeRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.api.domains.publications.repository import PublicationObjectRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: RequireExistingHierarchyCodeRuleConfig = RequireExistingHierarchyCodeRuleConfig(field="Hierarchy_Code")
    config.get_as_model.return_value = rule_config
    repository: Mock | PublicationObjectRepository = Mock(PublicationObjectRepository)
    repository.fetch_objects.return_value = [
        {
            "Code": "ambitie-1",
            "Hierarchy_Code": "beleidsdoel-1",  # connects to existing object
            "Object_ID": 1,
            "Object_Type": "ambitie",
        },
        {
            "Code": "beleidsdoel-1",
            "Hierarchy_Code": "beleidskeuze-1",  # connects to non-existing object
            "Object_ID": 1,
            "Object_Type": "beleidsdoel",
        },
        {
            "Code": "ambitie-2",  # no hierarchy code
            "Object_ID": 2,
            "Object_Type": "ambitie",
        },
    ]
    rule: RequireExistingHierarchyCodeRule = RequireExistingHierarchyCodeRule(config, repository)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="beleidsdoel",
                Object_ID="1",
                Code="beleidsdoel-1",
                Title="BD1 title",
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["beleidsdoel-1"]
    assert [error.object.title for error in errors] == ["BD1 title"]
