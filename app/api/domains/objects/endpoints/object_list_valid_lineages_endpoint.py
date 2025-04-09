from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.endpoint import BaseEndpointContext
from app.api.events.before_select_execution_event import BeforeSelectExecutionEvent
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.api.types import PreparedQuery
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    PaginatedQueryResult,
    Sort,
    SortedPagination,
    query_paginated,
)
from app.core.services.event.event_manager import EventManager
from app.core.types import Model


class ObjectListValidLineagesEndpointContext(BaseEndpointContext):
    object_type: str
    response_config_model: Model
    allowed_filter_columns: List[str]  # @todo: confirm if this is needed
    order_config: OrderConfig


@inject
def list_valid_lineages_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[ObjectListValidLineagesEndpointContext, Depends()],
) -> PagedResponse[BaseModel]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    prepared_query: PreparedQuery = object_repository.prepare_list_valid_lineages(context.object_type)
    prepare_query_event: BeforeSelectExecutionEvent = event_manager.dispatch(
        BeforeSelectExecutionEvent.create(
            query=prepared_query.query,
            response_model=context.response_config_model,
            objects_table_ref=prepared_query.aliased_ref,
        )
    )
    stmt: Select = prepare_query_event.payload.query
    paginated_result: PaginatedQueryResult = query_paginated(
        query=stmt,
        session=db,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=(getattr(prepared_query.aliased_ref, pagination.sort.column), pagination.sort.order),
    )

    rows: List[BaseModel] = [
        context.response_config_model.pydantic_model.model_validate(r) for r in paginated_result.items
    ]
    retrieved_objects_event: RetrievedObjectsEvent = event_manager.dispatch(
        RetrievedObjectsEvent.create(
            rows=rows,
            endpoint_id=context.builder_data.endpoint_id,
            response_model=context.response_config_model,
        )
    )

    return PagedResponse[BaseModel](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=retrieved_objects_event.payload.rows,
    )
