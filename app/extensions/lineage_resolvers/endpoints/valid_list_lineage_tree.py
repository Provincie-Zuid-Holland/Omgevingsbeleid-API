from typing import List, Type

from fastapi import APIRouter, Depends
import pydantic

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, Model, EndpointConfig
from app.dynamic.dependencies import (
    depends_event_dispatcher,
    depends_string_filters,
    depends_pagination,
)
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.event import RetrievedObjectsEvent
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import PagedResponse, Pagination, query_paginated
from app.dynamic.db.filters_converter import (
    FiltersConverterResult,
    convert_filters,
)


class ValidListLineageTreeEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
        response_model: Model,
        allowed_filter_columns: List[str],
    ):
        self._converter: Converter = converter
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model
        self._allowed_filter_columns: List[str] = allowed_filter_columns

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            filters: Filters = Depends(depends_string_filters),
            pagination: Pagination = Depends(depends_pagination),
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
        pagination: Pagination,
    ):
        filters.guard_keys(self._allowed_filter_columns)
        database_filter_result: FiltersConverterResult = convert_filters(filters)

        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == self._object_type)
            .filter(ObjectsTable.Object_ID == lineage_id)
        )

        paginated_result = query_paginated(
            query=stmt,
            session=db,
            limit=pagination.get_limit,
            offset=pagination.get_offset,
            sort=(ObjectsTable.Modified_Date, pagination.sort),
        )

        rows: List[self._response_type] = [
            self._response_type.from_orm(r) for r in paginated_result.items
        ]

        # Ask extensions for more information
        rows = self._run_events(rows, event_dispatcher)

        return PagedResponse[self._response_type](
            total=paginated_result.total_count,
            offset=pagination.get_offset,
            limit=pagination.get_limit,
            results=rows,
        )

    def _run_events(self, items: List[ObjectsTable], event_dispatcher: EventDispatcher):
        """
        Ask extensions for more information.
        """
        event: RetrievedObjectsEvent = event_dispatcher.dispatch(
            RetrievedObjectsEvent.create(
                items,
                self._endpoint_id,
                self._response_model,
            )
        )
        return event.payload.rows


class ValidListLineageTreeEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "valid_list_lineage_tree"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get(
            resolver_config.get("response_model"),
        )
        allowed_filter_columns: List[str] = resolver_config.get(
            "allowed_filter_columns", []
        )

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ValidListLineageTreeEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
        )
