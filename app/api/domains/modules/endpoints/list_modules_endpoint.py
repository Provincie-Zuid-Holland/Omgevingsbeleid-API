import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.api.domains.modules.types import Module
from app.api.domains.objects.dependencies import depends_filter_object_code
from app.api.domains.objects.types import FilterObjectCode
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    PaginatedQueryResult,
    Sort,
    SortedPagination,
)
from app.core.tables.users import UsersTable


class ListModulesEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_modules_endpoint(
    filter_object_code: Annotated[Optional[FilterObjectCode], Depends(depends_filter_object_code)],
    module_repository: Annotated[ModuleRepository, Depends(Provide[ApiContainer.module_repository])],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    context: Annotated[ListModulesEndpointContext, Depends()],
    only_mine: Annotated[bool, Query] = False,
    filter_activated: Optional[bool] = None,
    filter_closed: Optional[bool] = None,
    filter_successful: Optional[bool] = None,
    filter_title: Optional[str] = None,
) -> PagedResponse[Module]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    filter_on_me: Optional[uuid.UUID] = None
    if only_mine:
        filter_on_me = user.UUID

    paginated_result: PaginatedQueryResult = module_repository.get_with_filters(
        pagination=pagination,
        filter_activated=filter_activated,
        filter_closed=filter_closed,
        filter_successful=filter_successful,
        filter_title=filter_title,
        mine=filter_on_me,
        object_code=filter_object_code,
    )

    modules: List[Module] = [Module.model_validate(r) for r in paginated_result.items]

    return PagedResponse[Module](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=modules,
    )
