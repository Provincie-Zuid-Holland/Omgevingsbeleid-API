from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_status_repository import ModuleStatusRepository
from app.api.domains.modules.types import ModuleStatus
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable


@inject
def view_module_list_statuses_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    status_repository: Annotated[ModuleStatusRepository, Depends(Provide[ApiContainer.module_status_repository])],
) -> List[ModuleStatus]:
    statuses: List[ModuleStatusHistoryTable] = status_repository.get_all_by_module_id(session, module.Module_ID)

    response: List[ModuleStatus] = [ModuleStatus.model_validate(r) for r in statuses]
    return response
