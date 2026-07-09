from typing import Annotated, List

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.types import Module as ModuleClass
from app.api.domains.modules.types import ModuleStatus
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleTable
from app.core.tables.users import UsersTable


class ModuleOverviewResponse(BaseModel):
    Module: ModuleClass
    StatusHistory: List[ModuleStatus]


def view_module_overview_endpoint(
    module: Annotated[ModuleTable, Depends(depends_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
) -> ModuleOverviewResponse:
    status_history: List[ModuleStatus] = [ModuleStatus.model_validate(s) for s in module.status_history]

    response = ModuleOverviewResponse(
        Module=ModuleClass.model_validate(module),
        StatusHistory=status_history,
    )
    return response
