from typing import Optional

from fastapi import BackgroundTasks, Depends, HTTPException
from app.core.dependencies import depends_db
from sqlalchemy.orm import Session
from app.dynamic.db import ObjectStaticsTable

from app.dynamic.event_dispatcher import EventDispatcher, main_event_dispatcher
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.repository.object_static_repository import ObjectStaticRepository

from .utils.filters import Filters, FilterCombiner
from .utils.pagination import Pagination


def depends_event_dispatcher(
    background_tasks: BackgroundTasks,
    db: Session = Depends(depends_db),
) -> EventDispatcher:
    main_event_dispatcher.provide_db(db)
    main_event_dispatcher.provide_task_runner(background_tasks)
    return main_event_dispatcher


def depends_object_repository(
    db: Session = Depends(depends_db),
) -> ObjectRepository:
    return ObjectRepository(db)


def depends_object_static_repository(
    db: Session = Depends(depends_db),
) -> ObjectStaticRepository:
    return ObjectStaticRepository(db)


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


def depends_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> Pagination:
    return Pagination(
        offset=offset,
        limit=limit,
    )
