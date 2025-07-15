from typing import List
from app.api.domains.werkingsgebieden.endpoints.list_objects_by_geometry_endpoint import (
    ListObjectByGeometryEndpointContext,
    get_list_objects_by_geometry_endpoint,
)
from app.api.domains.werkingsgebieden.types import GeoSearchResult
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListObjectsByGeometryEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "areas_list_objects_by_geometry"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data

        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])
        area_object_type: str = resolver_config["area_object_type"]
        allowed_result_object_types: List[str] = resolver_config["allowed_result_object_types"]

        context = ListObjectByGeometryEndpointContext(
            area_object_type=area_object_type,
            allowed_result_object_types=allowed_result_object_types,
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_objects_by_geometry_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary="List the objects in werkingsgebieden by a geometry",
            description=None,
            tags=["Areas"],
        )
