from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.events.before_select_execution_event import BeforeSelectExecutionEvent
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    Sort,
    SortedPagination,
    query_paginated,
)
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable
from app.core.types import Model


class ModuleListLineageTreeEndpointContext(BaseEndpointContext):
    object_type: str
    endpoint_id: str
    response_config_model: Model
    order_config: OrderConfig
    allowed_filter_columns: List[str]


@inject
async def get_module_list_lineage_tree_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    lineage_id: int,
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    context: Annotated[ModuleListLineageTreeEndpointContext, Depends()],
) -> PagedResponse[BaseModel]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    stmt = (
        select(ModuleObjectsTable)
        .filter(ModuleObjectsTable.Module_ID == module.Module_ID)
        .filter(ModuleObjectsTable.Object_Type == context.object_type)
        .filter(ModuleObjectsTable.Object_ID == lineage_id)
    )
    query_event: BeforeSelectExecutionEvent = event_manager.dispatch(
        BeforeSelectExecutionEvent.create(
            query=stmt,
            response_model=context.response_config_model,
            objects_table_ref=ModuleObjectsTable,
        )
    )
    stmt = query_event.payload.query

    paginated_result = query_paginated(
        query=stmt,
        session=db,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=(getattr(ModuleObjectsTable, pagination.sort.column), pagination.sort.order),
    )

    rows: List[BaseModel] = [
        context.response_config_model.pydantic_model.model_validate(r) for r in paginated_result.items
    ]
    rows_event: RetrievedModuleObjectsEvent = event_manager.dispatch(
        RetrievedModuleObjectsEvent.create(
            rows,
            context.endpoint_id,
            context.response_config_model,
        )
    )
    rows = rows_event.payload.rows

    return PagedResponse[BaseModel](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=rows,
    )
