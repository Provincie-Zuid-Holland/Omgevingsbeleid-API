from datetime import datetime
from typing import List, Type

import pydantic
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, DynamicObjectModel, EndpointConfig, Model
from app.dynamic.db import ObjectsTable
from app.dynamic.db.filters_converter import FiltersConverterResult, convert_filters
from app.dynamic.dependencies import depends_event_dispatcher, depends_sorted_pagination_curried, depends_string_filters
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event import BeforeSelectExecutionEvent, RetrievedObjectsEvent
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination, query_paginated


class ValidListLineagesEndpoint(Endpoint):
    def __init__(
        self,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
        response_model: Model,
        allowed_filter_columns: List[str],
        order_config: OrderConfig,
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model
        self._allowed_filter_columns: List[str] = allowed_filter_columns
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            filters: Filters = Depends(depends_string_filters),
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            db: Session = Depends(depends_db),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> PagedResponse[self._response_type]:
            return self._handler(db, event_dispatcher, filters, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[self._response_type],
            summary=f"Get all the valid {self._object_type} lineages and shows the latest object of each",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        db: Session,
        event_dispatcher: EventDispatcher,
        filters: Filters,
        pagination: SortedPagination,
    ):
        filters.guard_keys(self._allowed_filter_columns)
        database_filter_result: FiltersConverterResult = convert_filters(filters)

        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.Object_Type == self._object_type)
            .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
            .subquery()
        )

        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.utcnow(),
                    subq.c.End_Validity == None,
                )
            )
        )

        event: BeforeSelectExecutionEvent = event_dispatcher.dispatch(
            BeforeSelectExecutionEvent.create(
                query=stmt,
                response_model=self._response_model,
                objects_table_ref=aliased_objects,
            )
        )
        stmt = event.payload.query

        paginated_result = query_paginated(
            query=stmt,
            session=db,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

        results: List[self._response_type] = []
        if paginated_result.total_count > 0:
            results = [self._response_type.model_validate(r) for r in paginated_result.items]
            results = self._run_events(results, event_dispatcher)

        return PagedResponse[self._response_type](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )

    def _run_events(self, dynamic_objects: List[pydantic.BaseModel], event_dispatcher: EventDispatcher):
        """
        Ask extensions for more information.
        """
        event: RetrievedObjectsEvent = event_dispatcher.dispatch(
            RetrievedObjectsEvent.create(
                rows=dynamic_objects,
                endpoint_id=self._endpoint_id,
                response_model=self._response_model,
            )
        )
        return event.payload.rows


class ValidListLineagesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "valid_list_lineages"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model: DynamicObjectModel = models_resolver.get(
            resolver_config.get("response_model"),
        )
        allowed_filter_columns: List[str] = resolver_config.get("allowed_filter_columns", [])
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ValidListLineagesEndpoint(
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
            order_config=order_config,
        )
