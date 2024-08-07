from typing import List, Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.dependencies import depends_acknowledged_relations_repository
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelation, build_from_orm
from app.extensions.acknowledged_relations.repository.acknowledged_relations_repository import (
    AcknowledgedRelationsRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_user


class EndpointHandler:
    def __init__(
        self,
        repository: AcknowledgedRelationsRepository,
        object_code: str,
        requested_by_us: bool,
        acknowledged: Optional[bool],
        show_inactive: Optional[bool],
    ):
        self._repository: AcknowledgedRelationsRepository = repository
        self._object_code: str = object_code
        self._requested_by_us: bool = requested_by_us
        self._acknowledged: Optional[bool] = acknowledged
        self._show_inactive: Optional[bool] = show_inactive

    def handle(self) -> List[AcknowledgedRelation]:
        table_rows: List[AcknowledgedRelationsTable] = self._repository.get_with_filters(
            code=self._object_code,
            requested_by_me=self._requested_by_us,
            acknowledged=self._acknowledged,
            show_inactive=self._show_inactive,
        )
        response: List[AcknowledgedRelation] = [build_from_orm(r, self._object_code) for r in table_rows]
        return response


class ListAcknowledgedRelationsEndpoint(Endpoint):
    def __init__(
        self,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            requested_by_us: bool = False,
            acknowledged: Optional[bool] = None,
            show_inactive: Optional[bool] = None,
            user: UsersTable = Depends(depends_current_user),
            repository: AcknowledgedRelationsRepository = Depends(depends_acknowledged_relations_repository),
        ) -> List[AcknowledgedRelation]:
            handler: EndpointHandler = EndpointHandler(
                repository,
                f"{self._object_type}-{lineage_id}",
                requested_by_us,
                acknowledged,
                show_inactive,
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
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
        )
