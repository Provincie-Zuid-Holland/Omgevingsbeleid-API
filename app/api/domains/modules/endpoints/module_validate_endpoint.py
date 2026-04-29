from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.services import ValidateModuleRunner
from app.api.domains.modules.services.validate_module_service import (
    ValidateModuleResult,
)
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleTable
from app.core.tables.users import UsersTable


@inject
def get_module_validate_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_module)],
    session: Annotated[Session, Depends(depends_db_session)],
    validate_module_runner: Annotated[ValidateModuleRunner, Depends(Provide[ApiContainer.validate_module_runner])],
) -> ValidateModuleResult:
    result: ValidateModuleResult = validate_module_runner.run(
        session,
        module.Module_ID,
    )
    return result
