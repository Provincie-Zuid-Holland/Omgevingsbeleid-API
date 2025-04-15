import uuid
from datetime import datetime
from typing import Annotated, Optional

from dependency_injector.wiring import inject
from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.modules.dependencies import depends_active_module_object_context
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.types import UserShort
from app.core.tables.modules import ModuleObjectContextTable
from app.core.tables.users import UsersTable


class ModuleObjectContext(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str

    Created_Date: datetime
    Modified_Date: datetime

    Action: str
    Explanation: str
    Conclusion: str

    Original_Adjust_On: Optional[uuid.UUID] = None

    Created_By: Optional[UserShort] = None
    Modified_By: Optional[UserShort] = None
    model_config = ConfigDict(from_attributes=True)


@inject
async def get_module_get_object_context_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    object_context: Annotated[ModuleObjectContextTable, Depends(depends_active_module_object_context)],
) -> ModuleObjectContext:
    response: ModuleObjectContext = ModuleObjectContext.model_validate(object_context)
    return response
