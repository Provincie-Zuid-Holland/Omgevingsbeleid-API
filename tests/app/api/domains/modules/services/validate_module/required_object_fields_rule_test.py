from unittest.mock import Mock

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    RequiredObjectFieldsRule,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.core.tables.modules import ModuleObjectsTable


class Ambitie(BaseModel):
    title: str = Field(..., min_length=5)

    model_config = ConfigDict(from_attributes=True)


def test_validate():
    object_map: dict[str, type[BaseModel]] = {
        "ambitie": Ambitie,
    }
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="1",
                code="ambitie-1",
                title="Obj",  # title too short
            ),
            ModuleObjectsTable(
                object_type="ambitie",
                object_id="2",
                code="ambitie-2",
                title="Object valid",
            ),
            ModuleObjectsTable(
                object_type="beleidsdoel",  # Object type not in map
                object_id="1",
                code="beleidsdoel-1",
                title="Some beleidsdoel",
            ),
        ],
    )
    rule = RequiredObjectFieldsRule(object_map)
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["ambitie-1"]
