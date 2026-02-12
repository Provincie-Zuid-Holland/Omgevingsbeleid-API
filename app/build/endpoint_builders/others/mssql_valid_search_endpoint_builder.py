from typing import Union, Dict

from pydantic import BaseModel

from app.api.domains.others.endpoints.mssql_valid_search_endpoint import (
    MssqlValidSearchEndpointContext,
    get_mssql_valid_search_endpoint,
)
from app.api.domains.others.types import ValidSearchConfig, ValidSearchObject
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.services.models_provider import ModelsProvider


class MssqlValidSearchEndpointBuilder(EndpointBuilder):
    def __init__(self, model_dynamic_type_builder: ModelDynamicTypeBuilder):
        self._model_dynamic_type_builder: ModelDynamicTypeBuilder = model_dynamic_type_builder

    def get_id(self) -> str:
        return "mssql_valid_search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        search_config: ValidSearchConfig = ValidSearchConfig(**resolver_config)
        model_map: Dict[str, str] = resolver_config["model_map"]
        response_model_name: str = resolver_config["response_model_name"]

        context = MssqlValidSearchEndpointContext(
            search_config=search_config,
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(get_mssql_valid_search_endpoint, context)

        union_object_type: Union[BaseModel] = self._model_dynamic_type_builder.build_object_union_type(model_map)
        response_type = PagedResponse[ValidSearchObject[union_object_type]]
        response_type.__name__ = response_model_name

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=response_type,
            summary="Search for valid objects",
            description=None,
            tags=["Search"],
        )
