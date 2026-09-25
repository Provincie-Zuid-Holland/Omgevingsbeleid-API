from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    CheckEmptyAreaDesignationTextConfig,
    CheckEmptyAreaDesignationTextRule,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: CheckEmptyAreaDesignationTextConfig = CheckEmptyAreaDesignationTextConfig(
        fields=["description"],
    )
    config.get_as_model.return_value = rule_config
    rule: CheckEmptyAreaDesignationTextRule = CheckEmptyAreaDesignationTextRule(config)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="beleidsdoel",
                object_id="1",
                code="beleidsdoel-1",
                title="BD1 title",
                description="""<p>BD1 <a data-hint-type="gebiedsaanwijzing" data-code="gebiedsaanwijzing-1">description</a></p>""",
            ),
            ModuleObjectsTable(
                object_type="beleidsdoel",  # empty gebiedsaanwijzing label
                object_id="2",
                code="beleidsdoel-2",
                title="BD2 title",
                description="""<p>BD2 <a data-hint-type="gebiedsaanwijzing" data-code="gebiedsaanwijzing-2"></a></p>""",
            ),
        ],
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["beleidsdoel-2"]
