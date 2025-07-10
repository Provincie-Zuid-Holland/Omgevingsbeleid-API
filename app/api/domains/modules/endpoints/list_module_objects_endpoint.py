import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import ModuleObjectActionFull, ModuleObjectShort, ModuleStatusCode
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class ModuleObjectsResponse(ModuleObjectShort):
    Status: str


class ListModuleObjectsEndpointContext(BaseEndpointContext):
    object_type: str
    order_config: OrderConfig


@inject
def get_list_module_objects_endpoint(
    object_type: Annotated[Optional[str], None],
    owner_uuid: Annotated[Optional[uuid.UUID], None],
    minimum_status: Annotated[Optional[ModuleStatusCode], None],
    only_active_modules: Annotated[bool, True],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    _: Annotated[UsersTable, Depends(depends_current_user)],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    context: Annotated[ListModuleObjectsEndpointContext, Depends()],
    actions: Annotated[List[ModuleObjectActionFull], Query] = [],
) -> PagedResponse[ModuleObjectsResponse]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result = module_object_repository.get_all_latest(
        pagination=pagination,
        only_active_modules=only_active_modules,
        minimum_status=minimum_status,
        owner_uuid=owner_uuid,
        object_type=object_type,
        actions=actions,
    )

    rows: List[ModuleObjectsResponse] = [
        ModuleObjectsResponse(
            Module_ID=mo.Module_ID,
            Status=status,
            Object_Type=mo.Object_Type,
            Object_ID=mo.Object_ID,
            Code=mo.Code,
            UUID=mo.UUID,
            Modified_Date=mo.Modified_Date,
            Title=mo.Title,
            ObjectStatics=mo.ObjectStatics,
            ModuleObjectContext=mo.ModuleObjectContext,
        )
        for mo, status in paginated_result.items
    ]

    return PagedResponse(
        total=paginated_result.total_count,
        limit=pagination.limit,
        offset=pagination.offset,
        results=rows,
    )
