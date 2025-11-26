from typing import Dict, Union

from pydantic import BaseModel


from app.api.domains.objects.endpoints.object_list_all_latest_endpoint import (
    ObjectListAllLatestResponse,
    ObjectListAllLatestEndpointContext,
    do_list_all_latest_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.services.models_provider import ModelsProvider


class ObjectListAllLatestEndpointBuilder(EndpointBuilder):
    def __init__(self, model_dynamic_type_builder: ModelDynamicTypeBuilder):
        self._model_dynamic_type_builder: ModelDynamicTypeBuilder = model_dynamic_type_builder

    def get_id(self) -> str:
        return "list_all_latest_objects"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])
        model_map: Dict[str, str] = resolver_config["model_map"]
        response_model_name: str = resolver_config["response_model_name"]

        context = ObjectListAllLatestEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(do_list_all_latest_endpoint, context)

        union_object_type: Union[BaseModel] = self._model_dynamic_type_builder.build_object_union_type(model_map)
        response_type = PagedResponse[ObjectListAllLatestResponse[union_object_type]]
        response_type.__name__ = response_model_name

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=response_type,
            summary="List all objects by object type filter",
            tags=["Objects"],
        )
