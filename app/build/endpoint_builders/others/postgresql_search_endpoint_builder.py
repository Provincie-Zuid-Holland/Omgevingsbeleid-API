from typing import Dict, Union

from pydantic import BaseModel

from app.api.domains.others.endpoints.postgres_search_endpoint import (
    get_postgresql_search_endpoint,
    PostgresqlSearchEndpointContext,
)
from app.api.domains.others.types import SearchObject, ValidSearchConfig
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.services.models_provider import ModelsProvider


class PostgresqlSearchEndpointBuilder(EndpointBuilder):
    def __init__(self, model_dynamic_type_builder: ModelDynamicTypeBuilder):
        self._model_dynamic_type_builder: ModelDynamicTypeBuilder = model_dynamic_type_builder

    def get_id(self) -> str:
        return "postgresql_search"

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

        context = PostgresqlSearchEndpointContext(
            search_config=search_config,
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(get_postgresql_search_endpoint, context)

        union_object_type: Union[BaseModel] = self._model_dynamic_type_builder.build_object_union_type(model_map)
        response_type = PagedResponse[SearchObject[union_object_type]]
        response_type.__name__ = response_model_name

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=response_type,
            summary="Search for objects",
            description=None,
            tags=["Search"],
        )
