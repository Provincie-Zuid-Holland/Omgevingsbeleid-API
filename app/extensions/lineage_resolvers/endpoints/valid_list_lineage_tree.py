from typing import List, Type

import pydantic
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, undefer_group

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.db import ObjectsTable
from app.dynamic.db.filters_converter import FiltersConverterResult, convert_filters
from app.dynamic.dependencies import depends_event_dispatcher, depends_sorted_pagination_curried, depends_string_filters
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event import RetrievedObjectsEvent
from app.dynamic.event.before_select_execution import BeforeSelectExecutionEvent
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination, query_paginated
from app.extensions.lineage_resolvers.db.next_object_version import NEXT_VERSION_COMPOSITE_GROUP


class ValidListLineageTreeEndpoint(Endpoint):
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
            lineage_id: int,
            filters: Filters = Depends(depends_string_filters),
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            db: Session = Depends(depends_db),
            event_dispatcher: Session = Depends(depends_event_dispatcher),
        ) -> PagedResponse[self._response_type]:
            return self._handler(db, event_dispatcher, lineage_id, filters, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[self._response_type],
            summary=f"Get all the valid {self._object_type} of a single lineage",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        db: Session,
        event_dispatcher: EventDispatcher,
        lineage_id: int,
        filters: Filters,
        pagination: SortedPagination,
    ):
        filters.guard_keys(self._allowed_filter_columns)
        database_filter_result: FiltersConverterResult = convert_filters(filters)

        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == self._object_type)
            .filter(ObjectsTable.Object_ID == lineage_id)
            .options(undefer_group(NEXT_VERSION_COMPOSITE_GROUP))
        )

        event: BeforeSelectExecutionEvent = event_dispatcher.dispatch(
            BeforeSelectExecutionEvent.create(
                query=stmt,
                response_model=self._response_model,
                objects_table_ref=ObjectsTable,
            )
        )
        stmt = event.payload.query

        paginated_result = query_paginated(
            query=stmt,
            session=db,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(ObjectsTable, pagination.sort.column), pagination.sort.order),
        )

        rows: List[self._response_type] = [self._response_type.model_validate(r) for r in paginated_result.items]

        # Ask extensions for more information
        rows = self._run_events(rows, event_dispatcher)

        return PagedResponse[self._response_type](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=rows,
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


class ValidListLineageTreeEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "valid_list_lineage_tree"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get(
            resolver_config.get("response_model"),
        )
        allowed_filter_columns: List[str] = resolver_config.get("allowed_filter_columns", [])
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ValidListLineageTreeEndpoint(
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
            order_config=order_config,
        )
