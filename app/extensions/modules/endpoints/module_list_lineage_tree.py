from typing import List, Type

from fastapi import APIRouter, Depends
import pydantic
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db
from app.core.utils.utils import table_to_dict

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
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import Pagination
from app.dynamic.db.filters_converter import (
    FiltersConverterResult,
    convert_filters,
)
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context_curried,
)
from app.extensions.modules.event.retrieved_module_objects_event import (
    RetrievedModuleObjectsEvent,
)
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleListLineageTreeEndpoint(Endpoint):
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
            user: GebruikersTable = Depends(depends_current_active_user),
            filters: Filters = Depends(depends_string_filters),
            pagination: Pagination = Depends(depends_pagination),
            module: ModuleTable = Depends(depends_active_module),
            module_object_context=Depends(
                depends_active_module_object_context_curried(self._object_type)
            ),
            db: Session = Depends(depends_db),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> List[self._response_type]:
            return self._handler(
                db, event_dispatcher, module, lineage_id, filters, pagination
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[self._response_type],
            summary=f"Get all the {self._object_type} of a single lineage in a module",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        db: Session,
        event_dispatcher: EventDispatcher,
        module: ModuleTable,
        lineage_id: int,
        filters: Filters,
        pagination: Pagination,
    ):
        filters.guard_keys(self._allowed_filter_columns)
        database_filter: FiltersConverterResult = convert_filters(filters)

        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.Module_ID == module.Module_ID)
            .filter(ModuleObjectsTable.Object_Type == self._object_type)
            .filter(ModuleObjectsTable.Object_ID == lineage_id)
            .order_by(desc(ModuleObjectsTable.Modified_Date))
            .limit(pagination.get_limit())
            .offset(pagination.get_offset())
        )

        # @todo: honor filters
        module_objects_tables: List[ModuleObjectsTable] = db.scalars(stmt).all()
        module_objects: List[dict] = [table_to_dict(t) for t in module_objects_tables]

        # Ask extensions for more information
        event: RetrievedModuleObjectsEvent = event_dispatcher.dispatch(
            RetrievedModuleObjectsEvent.create(
                module_objects,
                self._endpoint_id,
                self._response_model,
            )
        )
        rows = event.payload.rows

        deserialized_rows = self._converter.deserialize_list(self._object_id, rows)
        response = [self._response_type.parse_obj(row) for row in deserialized_rows]

        return response


class ModuleListLineageTreeEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_list_lineage_tree"

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
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ModuleListLineageTreeEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            allowed_filter_columns=allowed_filter_columns,
        )