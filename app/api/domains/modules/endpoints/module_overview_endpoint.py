from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel

from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.types import Module as ModuleClass
from app.api.domains.modules.types import ModuleStatus
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleTable
from app.core.tables.users import UsersTable


class ModuleOverviewResponse(BaseModel):
    module: ModuleClass
    status_history: list[ModuleStatus]


def view_module_overview_endpoint(
    module: Annotated[ModuleTable, Depends(depends_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
) -> ModuleOverviewResponse:
    status_history: list[ModuleStatus] = [ModuleStatus.model_validate(s) for s in module.status_history]

    response = ModuleOverviewResponse(
        module=ModuleClass.model_validate(module),
        status_history=status_history,
    )
    return response
