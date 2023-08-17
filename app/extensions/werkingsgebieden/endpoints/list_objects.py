from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_pagination_with_config_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, PaginatedQueryResult, Pagination
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user
from app.extensions.werkingsgebieden.dependencies import depends_werkingsgebieden_repository
from app.extensions.werkingsgebieden.models.models import GeoSearchResult
from app.extensions.werkingsgebieden.repository.werkingsgebieden_repository import WerkingsgebiedenRepository


class SearchGeoRequestData(BaseModel):
    Object_Types: Optional[List[str]]
    Area_List: List[UUID]

    class Config:
        arbitrary_types_allowed = True

    @validator("Area_List")
    def valid_area_list(cls, v):
        if len(v) < 1:
            raise ValueError("area_list requires more than 1 uuid")
        if len(v) > 300:
            raise ValueError("area_list is too large, max 300 items")
        return v

    @validator("Object_Types")
    def allowed_object_type(cls, v):
        # TODO: Config?
        allowed = [
            "ambitie",
            "beleidsdoel",
            "beleidskeuze",
            "beleidsregel",
            "maatregel",
            "gebiedsprogramma",
        ]

        for obj_type in v:
            if obj_type not in allowed:
                raise ValueError(f"object types allowed: {str(allowed)}")

        return v


class ListObjectsInGeoEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: SearchGeoRequestData,
            pagination: Pagination = Depends(depends_pagination_with_config_curried(self._order_config)),
            user: UsersTable = Depends(depends_current_active_user),
            repository: WerkingsgebiedenRepository = Depends(depends_werkingsgebieden_repository),
        ) -> PagedResponse[GeoSearchResult]:
            return self._handler(
                repository=repository,
                area_list=object_in.Area_List,
                object_types=object_in.Object_Types,
                pagination=pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary=f"List the objects active in werkingsgebieden",
            description=None,
            tags=["Search"],
        )

        return router

    def _handler(
        self,
        repository: WerkingsgebiedenRepository,
        area_list: List[UUID],
        pagination: Pagination,
        object_types: List[str] = None,
    ) -> PagedResponse[GeoSearchResult]:
        # TODO: add object_type validation
        paginated_result: PaginatedQueryResult = repository.get_latest_in_area(
            in_area=area_list,
            object_types=object_types,
            pagination=pagination,
        )
        object_list = []
        for item in paginated_result.items:
            search_result = GeoSearchResult(
                Gebied=str(item.Gebied_UUID),
                Titel=item.Title,
                Omschrijving=item.Description,
                Type=item.Object_Type,
                UUID=item.UUID,
            )
            object_list.append(search_result)

        return PagedResponse(
            total=paginated_result.total_count,
            limit=pagination.limit,
            offset=pagination.offset,
            results=object_list,
        )


class ListObjectsInGeoEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_objects_in_werkingsgebieden"

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

        return ListObjectsInGeoEndpoint(
            path=path,
            order_config=order_config,
        )
