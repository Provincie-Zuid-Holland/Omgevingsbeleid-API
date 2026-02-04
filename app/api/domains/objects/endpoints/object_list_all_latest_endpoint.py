import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.modules.types import GenericObjectShort
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination


class ObjectListAllLastestRequestData(BaseModel):
    Object_Types: Optional[List[str]]

class ObjectListAllLatestEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def do_list_all_latest_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[ObjectListAllLatestEndpointContext, Depends()],
    object_types: ObjectListAllLastestRequestData,
    owner_uuid: Optional[uuid.UUID] = None,
) -> PagedResponse[GenericObjectShort]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paged_result = object_repository.get_latest_filtered(
        session=session,
        pagination=pagination,
        owner_uuid=owner_uuid,
        object_types=object_types.Object_Types,
    )

    rows: List[GenericObjectShort] = [GenericObjectShort.model_validate(r) for r in paged_result.items]

    return PagedResponse[GenericObjectShort](
        total=paged_result.total_count,
        limit=pagination.limit,
        offset=pagination.offset,
        results=rows,
    )
