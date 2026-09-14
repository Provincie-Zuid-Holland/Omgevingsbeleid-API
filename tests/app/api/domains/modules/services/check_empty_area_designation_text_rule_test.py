from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services import CheckEmptyAreaDesignationTextRule
from app.api.domains.modules.services.validate_module_service import (
    CheckEmptyAreaDesignationTextConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: CheckEmptyAreaDesignationTextConfig = CheckEmptyAreaDesignationTextConfig(
        fields=["Description"],
    )
    config.get_as_model.return_value = rule_config
    rule: CheckEmptyAreaDesignationTextRule = CheckEmptyAreaDesignationTextRule(config)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="beleidsdoel",
                Object_ID="1",
                Code="beleidsdoel-1",
                Title="BD1 title",
                Description="""<p>BD1 <a data-hint-type="gebiedsaanwijzing" data-code="gebiedsaanwijzing-1">description</a></p>""",
            ),
            ModuleObjectsTable(
                Object_Type="beleidsdoel",  # empty gebiedsaanwijzing label
                Object_ID="2",
                Code="beleidsdoel-2",
                Title="BD2 title",
                Description="""<p>BD2 <a data-hint-type="gebiedsaanwijzing" data-code="gebiedsaanwijzing-2"></a></p>""",
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["beleidsdoel-2"]
