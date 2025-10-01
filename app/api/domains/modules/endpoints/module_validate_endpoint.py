from typing import Annotated, List
from datetime import datetime, timezone

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.services.validate_module_service import ValidateModuleResult, ValidateModuleService, \
    ValidateModuleRequest
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable


@inject
def get_module_validate_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_module)],
    session: Annotated[Session, Depends(depends_db_session)],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    validate_module_service: Annotated[ValidateModuleService, Depends(Provide[ApiContainer.validate_module_service])],
) -> ValidateModuleResult:
    module_objects: List[ModuleObjectsTable] = module_object_repository.get_objects_in_time(
        session,
        module.Module_ID,
        datetime.now(timezone.utc),
    )
    request = ValidateModuleRequest(module_id=module.Module_ID, module_objects=module_objects)

    result: ValidateModuleResult = validate_module_service.validate(session, request)
    return result
