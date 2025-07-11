from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.api.domains.modules.types import PublicModuleShort
from app.api.utils.pagination import PagedResponse, SimplePagination


@inject
def get_public_list_modules_endpoint(
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    module_repository: Annotated[ModuleRepository, Depends(Provide[ApiContainer.module_repository])],
) -> PagedResponse[PublicModuleShort]:
    paginated_result = module_repository.get_public_modules(session, pagination)

    modules: List[PublicModuleShort] = [
        PublicModuleShort(
            Module_ID=module.Module_ID,
            Title=module.Title,
            Description=module.Description,
            Status=status,
        )
        for status, module in paginated_result.items
    ]

    return PagedResponse[PublicModuleShort](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=modules,
    )
