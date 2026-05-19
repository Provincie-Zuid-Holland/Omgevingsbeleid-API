from typing import Annotated, Generic, List, Optional, Dict
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import and_, or_

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
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
    OptionalSort,
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    Sort,
    SortOrder,
    SortedPagination,
    query_paginated_no_scalars,
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


def _depends_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[SortOrder] = None,
) -> OptionalSortedPagination:
    optional_sort = OptionalSort(column=sort_column, order=sort_order)
    return OptionalSortedPagination(
        offset=offset,
        limit=limit if limit is not None else 50,
        sort=optional_sort,
    )


@inject
def get_list_module_detail_objects_endpoint(
    module: Annotated[ModuleTable, Depends(depends_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(_depends_pagination)],
    context: Annotated[ListModuleDetailObjectsEndpointContext, Depends()],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    object_type: Optional[str] = None,
    actions: Annotated[List[ModuleObjectActionFull], Query()] = [],
    mine: Annotated[bool, Query()] = False,
    query: Optional[str] = None,
) -> PagedResponse[ModuleDetailObjectsResponse]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)


    subq = (
        select(
            ModuleObjectsTable,
            ModuleObjectContextTable,
            ObjectStaticsTable,
            func.row_number()
            .over(
                partition_by=ModuleObjectsTable.Code,
                order_by=desc(ModuleObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        )
        .select_from(ModuleObjectsTable)
        .join(ModuleObjectsTable.ObjectStatics)
        .join(ModuleObjectsTable.ModuleObjectContext)
        .filter(ModuleObjectsTable.Module_ID == module.Module_ID)
        .filter(ModuleObjectContextTable.Hidden == False)
    )

    filters = [
        ModuleObjectsTable.Object_Type == object_type if object_type is not None else None,
        ModuleObjectContextTable.Action.in_(actions) if actions else None,
        ModuleObjectsTable.Title.like(f"%{query}%") if query is not None else None,
        (
            or_(
                ObjectStaticsTable.Owner_1_UUID == user.UUID,
                ObjectStaticsTable.Owner_2_UUID == user.UUID,
            ).self_group()
            if mine
            else None
        ),
    ]
    active_filters = [f for f in filters if f is not None]
    if active_filters:
        subq = subq.filter(and_(*active_filters))

    subq = subq.subquery()
    aliased_objects = aliased(ModuleObjectsTable, subq)
    aliased_object_statics = aliased(ObjectStaticsTable, subq)
    aliased_module_object_context = aliased(ModuleObjectContextTable, subq)

    stmt = (
        select(
            aliased_objects,
            aliased_object_statics,
            aliased_module_object_context,
        )
        .filter(subq.c._RowNumber == 1)
        .filter(subq.c.Deleted == False)
    )

    paginated_result = query_paginated_no_scalars(
        query=stmt,
        session=session,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
    )

    rows: List[ModuleDetailObjectsResponse] = []
    for object_table, object_static, module_object_context in paginated_result.items:
        parsed_model: BaseModel = module_objects_to_models_parser.parse(object_table, context.model_map)
        if object_table.Object_Type == "beleidsdoel":
            parsed_model.__dict__.pop("Description", None)
        response: ModuleDetailObjectsResponse = ModuleDetailObjectsResponse(
            Module_ID=module.Module_ID,
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
