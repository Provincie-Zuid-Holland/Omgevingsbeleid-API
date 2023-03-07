from typing import List, Optional

from fastapi import APIRouter, Depends

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.dependencies import (
    depends_acknowledged_relations_repository,
)
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelation
from app.extensions.acknowledged_relations.repository.acknowledged_relations_repository import (
    AcknowledgedRelationsRepository,
)
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_user


class EndpointHandler:
    def __init__(
        self,
        repository: AcknowledgedRelationsRepository,
        object_code: str,
        requested_by_us: bool,
        acknowledged: Optional[bool],
    ):
        self._repository: AcknowledgedRelationsRepository = repository
        self._object_code: str = object_code
        self._requested_by_us: bool = requested_by_us
        self._acknowledged: Optional[bool] = acknowledged

    def handle(self) -> List[AcknowledgedRelation]:
        table_rows: List[
            AcknowledgedRelationsTable
        ] = self._repository.get_with_filters(
            self._object_code,
            self._requested_by_us,
            self._acknowledged,
        )
        response: List[AcknowledgedRelation] = [
            r.as_model(self._object_code) for r in table_rows
        ]
        return response


class ListAcknowledgedRelationsEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
    ):
        self._converter: Converter = converter
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            requested_by_us: bool = False,
            acknowledged: Optional[bool] = None,
            user: GebruikersTable = Depends(depends_current_user),
            repository: AcknowledgedRelationsRepository = Depends(
                depends_acknowledged_relations_repository
            ),
        ) -> List[AcknowledgedRelation]:
            handler: EndpointHandler = EndpointHandler(
                repository,
                f"{self._object_type}-{lineage_id}",
                requested_by_us,
                acknowledged,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[AcknowledgedRelation],
            summary=f"Get all acknowledged relations of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class ListAcknowledgedRelationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_acknowledged_relations"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ListAcknowledgedRelationsEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
        )
