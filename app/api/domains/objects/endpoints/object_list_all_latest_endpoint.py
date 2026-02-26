import uuid
from typing import Annotated, List, Optional, Generic, Sequence, Tuple, Dict

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.modules.types import ObjectStaticShort
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.others.types import TModel
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    Sort,
    SortedPagination,
    PaginatedQueryResult,
)
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable


class ObjectListAllLatestResponse(BaseModel, Generic[TModel]):
    Object_Type: str
    ObjectStatics: ObjectStaticShort
    Model: TModel

    model_config = ConfigDict(from_attributes=True, title="ModuleObjectsResponse")


class ObjectListAllLatestEndpointContext(BaseEndpointContext):
    order_config: OrderConfig
    model_map: Dict[str, str]


@inject
def do_list_all_latest_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[ObjectListAllLatestEndpointContext, Depends()],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    object_types: Annotated[Optional[List[str]], Query(alias="object_types")] = None,
    owner_uuid: Optional[uuid.UUID] = None,
) -> PagedResponse[ObjectListAllLatestResponse[BaseModel]]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result: PaginatedQueryResult = object_repository.get_latest_filtered(
        session=session,
        pagination=pagination,
        owner_uuid=owner_uuid,
        object_types=object_types
    )
    paginated_items: Sequence[Tuple[ObjectsTable, ObjectStaticsTable]] = paginated_result.items

    objects: List[ObjectListAllLatestResponse[BaseModel]] = []
    for object_current, object_static in paginated_items:
        parsed_model: BaseModel = module_objects_to_models_parser.parse(object_current, context.model_map)
        object_response = ObjectListAllLatestResponse(
            Object_Type=object_current.Object_Type,
            ObjectStatics=object_static,
            Model=parsed_model,
        )
        objects.append(object_response)

    return PagedResponse[ObjectListAllLatestResponse[BaseModel]](
        total=paginated_result.total_count,
        limit=pagination.limit,
        offset=pagination.offset,
        results=objects,
    )
