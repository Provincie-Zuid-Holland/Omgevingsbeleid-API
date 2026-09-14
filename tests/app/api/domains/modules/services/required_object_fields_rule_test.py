from unittest.mock import Mock

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.domains.modules.services import RequiredObjectFieldsRule
from app.api.domains.modules.services.validate_module_service import ValidateModuleError, ValidateModuleRequest
from app.core.tables.modules import ModuleObjectsTable


class Ambitie(BaseModel):
    Title: str = Field(..., min_length=5)

    model_config = ConfigDict(from_attributes=True)


def test_validate():
    object_map: dict[str, type[BaseModel]] = {
        "ambitie": Ambitie,
    }
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="1",
                Code="ambitie-1",
                Title="Obj",  # Title too short
            ),
            ModuleObjectsTable(
                Object_Type="ambitie",
                Object_ID="2",
                Code="ambitie-2",
                Title="Object valid",
            ),
            ModuleObjectsTable(
                Object_Type="beleidsdoel",  # Object type not in map
                Object_ID="1",
                Code="beleidsdoel-1",
                Title="Some beleidsdoel",
            ),
        ],
    )
    rule = RequiredObjectFieldsRule(object_map)
    db: Mock | Session = Mock(Session)
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == ["ambitie-1"]
