from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_object_repository, depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination


class GenericObjectShort(BaseModel):
    Object_Type: str
    Object_ID: int
    UUID: UUID
    Title: Optional[str]

    class Config:
        orm_mode = True


class ListAllLatestObjectsEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            owner_uuid: Optional[UUID] = None,  # Depends user exists
            object_type: Optional[str] = None,  # Depends user exists
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            object_repository: ObjectRepository = Depends(depends_object_repository),
        ):
            return self._handler(owner_uuid, object_type, pagination, object_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[GenericObjectShort],
            summary=f"List all objects filterable in short format",
            description=None,
            tags=["Search"],
        )

        return router

    def _handler(
        self,
        owner_uuid: Optional[UUID],
        object_type: Optional[str],
        pagination: SortedPagination,
        object_repo: ObjectRepository,
    ):
        paged_result = object_repo.get_latest_filtered(
            pagination=pagination,
            owner_uuid=owner_uuid,
            object_type=object_type,
        )

        # Cast to pyd model
        rows: List[GenericObjectShort] = [GenericObjectShort.from_orm(r) for r in paged_result.items]

        return PagedResponse[GenericObjectShort](
            total=paged_result.total_count,
            limit=pagination.limit,
            offset=pagination.offset,
            results=rows,
        )


class ListAllLatestObjectsResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_all_latest_objects"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ListAllLatestObjectsEndpoint(
            path=path,
            order_config=order_config,
        )
