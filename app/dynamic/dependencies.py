import uuid
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.event_listeners import EventListeners
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.repository.object_static_repository import ObjectStaticRepository

from .utils.filters import FilterCombiner, Filters
from .utils.pagination import OrderConfig, SimplePagination, Sort, SortedPagination, SortOrder


def depends_event_dispatcher(
    request: Request,
    db: Session = Depends(depends_db),
) -> EventDispatcher:
    event_listeners: EventListeners = request.app.state.event_listeners
    return EventDispatcher(event_listeners, db)


def depends_object_repository(
    db: Session = Depends(depends_db),
) -> ObjectRepository:
    return ObjectRepository(db)


def depends_object_static_repository(
    db: Session = Depends(depends_db),
) -> ObjectStaticRepository:
    return ObjectStaticRepository(db)


def depends_object_by_uuid(
    uuid: uuid.UUID,
    repository: ObjectRepository = Depends(depends_object_repository),
):
    maybe_object: Optional[ObjectsTable] = repository.get_by_uuid(uuid)
    if not maybe_object:
        raise HTTPException(status_code=404, detail="Object niet gevonden")
    return maybe_object


def depends_object_static_by_object_type_and_id(
    object_type: str,
    lineage_id: int,
    repository: ObjectStaticRepository = Depends(depends_object_static_repository),
):
    maybe_static: Optional[ObjectStaticsTable] = repository.get_by_object_type_and_id(
        object_type,
        lineage_id,
    )
    if not maybe_static:
        raise HTTPException(status_code=404, detail="Object static niet gevonden")
    return maybe_static


def depends_object_static_by_object_type_and_id_curried(object_type: str) -> Callable:
    def depends_object_static_by_object_type_and_id_inner(
        lineage_id: int,
        repository: ObjectStaticRepository = Depends(depends_object_static_repository),
    ):
        return depends_object_static_by_object_type_and_id(object_type, lineage_id, repository)

    return depends_object_static_by_object_type_and_id_inner


def depends_string_filters(
    all_filters: Optional[str] = None,
    any_filters: Optional[str] = None,
) -> Filters:
    filters = Filters()
    if all_filters:
        filters.add_from_string(FilterCombiner.AND, all_filters)

    if any_filters:
        filters.add_from_string(FilterCombiner.OR, any_filters)

    return filters


def depends_simple_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> SimplePagination:
    return SimplePagination(offset=offset, limit=limit)


def depends_sorted_pagination_curried(config: OrderConfig) -> Callable:
    def depends_sorted_pagination_inner(
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
    ) -> SortedPagination:
        sort_result: Sort = config.get_sort(sort_column, sort_order)
        pagination: SortedPagination = SortedPagination(
            offset=offset,
            limit=limit,
            sort=sort_result,
        )
        return pagination

    return depends_sorted_pagination_inner


class FilterObjectCode(BaseModel):
    object_type: str
    lineage_id: int

    def get_code(self) -> str:
        return f"{self.object_type}-{self.lineage_id}"


def depends_filter_object_code(
    object_type: Optional[str] = None,
    lineage_id: Optional[int] = None,
) -> Optional[FilterObjectCode]:
    if object_type is None and lineage_id is None:
        return None

    if object_type is None or lineage_id is None:
        raise ValueError("object_type and object_lineage_id should be supplied together.")

    return FilterObjectCode(
        object_type=object_type,
        lineage_id=lineage_id,
    )
