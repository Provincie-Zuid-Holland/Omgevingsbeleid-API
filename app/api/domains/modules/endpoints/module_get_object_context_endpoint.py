import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.modules.dependencies import depends_active_module_object_context
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.types import UserShort
from app.core.tables.modules import ModuleObjectContextTable
from app.core.tables.users import UsersTable


class ModuleObjectContext(BaseModel):
    module_id: int
    object_type: str
    object_id: int
    code: str

    created_date: datetime
    modified_date: datetime

    action: str
    explanation: str
    conclusion: str

    original_adjust_on: uuid.UUID | None = None

    created_by: UserShort | None = None
    modified_by: UserShort | None = None

    model_config = ConfigDict(from_attributes=True)


def get_module_get_object_context_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    object_context: Annotated[ModuleObjectContextTable, Depends(depends_active_module_object_context)],
) -> ModuleObjectContext:
    response: ModuleObjectContext = ModuleObjectContext.model_validate(object_context)
    return response
