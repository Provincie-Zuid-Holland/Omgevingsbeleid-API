from datetime import datetime
from typing import List, Type

from fastapi import APIRouter, Depends
import pydantic
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.db import ObjectStaticsTable

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
from app.dynamic.utils.pagination import Pagination
from app.dynamic.db.filters_converter import (
    FiltersConverterResult,
    convert_filters,
)


class ValidListLineagesEndpoint(Endpoint):
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
            filters: Filters = Depends(depends_string_filters),
            pagination: Pagination = Depends(depends_pagination),
            db: Session = Depends(depends_db),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> List[self._response_type]:
            return self._handler(db, event_dispatcher, filters, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[self._response_type],
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
        pagination: Pagination,
    ):
        filters.guard_keys(self._allowed_filter_columns)
        database_filter_result: FiltersConverterResult = convert_filters(filters)

        subq = (
            select(
                ObjectsTable,
                ObjectStaticsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .join(ObjectStaticsTable)
            .filter(ObjectsTable.Object_Type == self._object_type)
            .filter(ObjectsTable.Start_Validity <= datetime.now())
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(),
                    subq.c.End_Validity == None,
                )
            )
            .limit(pagination.get_limit())
            .offset(pagination.get_offset())
        )

        table_rows = db.execute(stmt).all()
        rows = [r._asdict() for r in table_rows]
        if not rows:
            return []

        # Ask extensions for more information
        event: RetrievedObjectsEvent = event_dispatcher.dispatch(
            RetrievedObjectsEvent.create(
                rows,
                self._endpoint_id,
                self._response_model,
            )
        )
        rows = event.payload.rows

        deserialized_rows = self._converter.deserialize_list(self._object_id, rows)
        response = [self._response_type.parse_obj(row) for row in deserialized_rows]

        return response


class ValidListLineagesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "valid_list_lineages"

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
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ValidListLineagesEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
        )
