from enum import Enum
import uuid
from typing import Annotated, Generic, List, Optional, Dict, Sequence, Tuple

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository, OwnerFilter
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.modules.types import (
    ModuleObjectActionFull,
    ModuleObjectContextShort,
    ModuleStatusCode,
    ObjectStaticShort,
)
from app.api.domains.others.types import TModel
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
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable


class ModuleObjectsResponse(BaseModel, Generic[TModel]):
    Module_ID: int
    Module_Latest_Status: str

    Object_Type: str
    ObjectStatics: ObjectStaticShort
    ModuleObjectContext: ModuleObjectContextShort
    Model: TModel

    model_config = ConfigDict(from_attributes=True, title="ModuleObjectsResponse")


class ListModuleObjectsEndpointContext(BaseEndpointContext):
    order_config: OrderConfig
    model_map: Dict[str, str]


class OwnerType(str, Enum):
    ALL = "All"
    MINE = "Mine"
    OTHERS = "Others"


@inject
def get_list_module_objects_endpoint(
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    _: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    context: Annotated[ListModuleObjectsEndpointContext, Depends()],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    object_types: Annotated[List[str], Query()] = [],
    owner_uuid: Optional[uuid.UUID] = None,
    owner_type: OwnerType = OwnerType.ALL,
    minimum_status: Optional[ModuleStatusCode] = None,
    only_active_modules: bool = True,
    title: Optional[str] = None,
    actions: Annotated[List[ModuleObjectActionFull], Query()] = [],
    module_id: Optional[int] = None,
) -> PagedResponse[ModuleObjectsResponse]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    owner_filter: Optional[OwnerFilter] = None
    match (owner_type, owner_uuid):
        case (OwnerType.MINE, uuid.UUID()):
            owner_filter = OwnerFilter(is_mine=True, owner_uuid=owner_uuid)
        case (OwnerType.OTHERS, uuid.UUID()):
            owner_filter = OwnerFilter(is_mine=False, owner_uuid=owner_uuid)
        case (OwnerType.ALL, _):
            pass
        case _:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "owner_uuid is required when owner_type is 'Mine' or 'Others'",
            )

    paginated_result: PaginatedQueryResult = module_object_repository.get_all_latest(
        session=session,
        pagination=pagination,
        only_active_modules=only_active_modules,
        minimum_status=minimum_status,
        owner_filter=owner_filter,
        object_types=object_types,
        title=title,
        actions=actions,
        module_id=module_id,
    )
    paginated_items: Sequence[Tuple[ModuleObjectsTable, ObjectStaticsTable, ModuleObjectContextTable, str]] = (
        paginated_result.items
    )

    rows: List[ModuleObjectsResponse] = []
    for object_table, object_static, module_object_context, module_status in paginated_items:
        parsed_model: BaseModel = module_objects_to_models_parser.parse(object_table, context.model_map)
        response: ModuleObjectsResponse = ModuleObjectsResponse(
            Module_ID=module_object_context.Module_ID,
            Module_Latest_Status=module_status,
            Model=parsed_model,
            ObjectStatics=ObjectStaticShort.model_validate(object_static),
            ModuleObjectContext=ModuleObjectContextShort.model_validate(module_object_context),
            Object_Type=object_table.Object_Type,
        )
        rows.append(response)

    return PagedResponse(
        total=paginated_result.total_count,
        limit=pagination.limit,
        offset=pagination.offset,
        results=rows,
    )
