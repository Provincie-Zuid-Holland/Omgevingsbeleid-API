from typing import Annotated, Generic, List, Optional, Dict
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased, joinedload
from sqlalchemy.sql import and_, or_

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.modules.types import (
    ModuleObjectActionFull,
    ModuleObjectContextShort,
    ObjectStaticShort,
)
from app.api.domains.others.types import TModel
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    Sort,
    SortedPagination,
    query_paginated,
)
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable


class ModuleDetailObjectsResponse(BaseModel, Generic[TModel]):
    Module_ID: int
    Object_Type: str
    ObjectStatics: ObjectStaticShort
    ModuleObjectContext: ModuleObjectContextShort
    Model: TModel

    model_config = ConfigDict(from_attributes=True, title="ModuleDetailObjectsResponse")


class ListModuleDetailObjectsEndpointContext(BaseEndpointContext):
    order_config: OrderConfig
    model_map: Dict[str, str]


@inject
def get_list_module_detail_objects_endpoint(
    module: Annotated[ModuleTable, Depends(depends_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    context: Annotated[ListModuleDetailObjectsEndpointContext, Depends()],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    object_type: Optional[str] = None,
    actions: Annotated[List[ModuleObjectActionFull], Query()] = [],
    mine: Annotated[bool, Query()] = False,
    title: Optional[str] = None,
) -> PagedResponse[ModuleDetailObjectsResponse]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    subq = (
        select(
            ModuleObjectsTable,
            func.row_number()
            .over(
                partition_by=ModuleObjectsTable.Code,
                order_by=desc(ModuleObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        )
        .join(ModuleObjectsTable.ModuleObjectContext)
        .filter(ModuleObjectsTable.Module_ID == module.Module_ID)
        .filter(ModuleObjectContextTable.Hidden == False)
        .subquery()
    )

    aliased_objects = aliased(ModuleObjectsTable, subq)
    stmt = (
        select(aliased_objects)
        .filter(subq.c._RowNumber == 1)
        .filter(subq.c.Deleted == False)
        .options(
            joinedload(aliased_objects.ModuleObjectContext),
            joinedload(aliased_objects.ObjectStatics),
        )
    )

    filters = [
        subq.c.Object_Type == object_type if object_type is not None else None,
        subq.c.Title.like(title) if title is not None else None,
    ]

    if actions:
        stmt = stmt.join(aliased_objects.ModuleObjectContext).filter(ModuleObjectContextTable.Action.in_(actions))

    if mine:
        stmt = stmt.join(aliased_objects.ObjectStatics).filter(
            or_(
                ObjectStaticsTable.Owner_1_UUID == user.UUID,
                ObjectStaticsTable.Owner_2_UUID == user.UUID,
            )
        )

    active_filters = [f for f in filters if f is not None]
    if active_filters:
        stmt = stmt.filter(and_(*active_filters))

    paginated_result = query_paginated(
        query=stmt,
        session=session,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
    )

    rows: List[ModuleDetailObjectsResponse] = []
    for object_table in paginated_result.items:
        parsed_model: BaseModel = module_objects_to_models_parser.parse(object_table, context.model_map)
        response: ModuleDetailObjectsResponse = ModuleDetailObjectsResponse(
            Module_ID=object_table.Module_ID,
            Model=parsed_model,
            ObjectStatics=ObjectStaticShort.model_validate(object_table.ObjectStatics),
            ModuleObjectContext=ModuleObjectContextShort.model_validate(object_table.ModuleObjectContext),
            Object_Type=object_table.Object_Type,
        )
        rows.append(response)

    return PagedResponse(
        total=paginated_result.total_count,
        limit=pagination.limit,
        offset=pagination.offset,
        results=rows,
    )
