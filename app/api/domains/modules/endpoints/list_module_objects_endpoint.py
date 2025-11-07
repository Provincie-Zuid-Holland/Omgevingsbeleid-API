import uuid
from typing import Annotated, Generic, List, Optional, Dict, Sequence, Tuple, TypeVar

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.modules.types import (
    ModuleObjectActionFull,
    ModuleObjectContextShort,
    ModuleStatusCode,
    ObjectStaticShort,
)
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


TModel = TypeVar("TModel", bound=BaseModel)


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
    object_type: Optional[str] = None,
    owner_uuid: Optional[uuid.UUID] = None,
    minimum_status: Optional[ModuleStatusCode] = None,
    only_active_modules: bool = True,
    title: Optional[str] = None,
    actions: Annotated[List[ModuleObjectActionFull], Query(default_factory=list)] = [],
) -> PagedResponse[ModuleObjectsResponse]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result: PaginatedQueryResult = module_object_repository.get_all_latest(
        session=session,
        pagination=pagination,
        only_active_modules=only_active_modules,
        minimum_status=minimum_status,
        owner_uuid=owner_uuid,
        object_type=object_type,
        title=title,
        actions=actions,
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
