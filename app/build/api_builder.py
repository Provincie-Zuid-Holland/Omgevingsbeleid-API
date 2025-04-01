from typing import List
from sqlalchemy.orm import Session

from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint
from app.build.endpoint_builders.endpoint_builder_provider import EndpointBuilderProvider
from app.build.objects.types import BuildData, EndpointConfig, Model
from app.build.services.config_parser import ConfigParser
from app.build.services.model_provider import ModelProvider
from app.core.settings import Settings


class ApiBuilder:
    def __init__(
        self,
        settings: Settings,
        db: Session,
        config_parser: ConfigParser,
        endpoint_builder_provider: EndpointBuilderProvider,
        declared_models: List[Model],
    ):
        self._settings: Settings = settings
        self._db: Session = db
        self._config_parser: ConfigParser = config_parser
        self._endpoint_builder_provider: EndpointBuilderProvider = endpoint_builder_provider
        self._declared_models: List[Model] = declared_models

    def build(self):
        build_data: BuildData = self._config_parser.parse(
            self._settings.MAIN_CONFIG_FILE,
            self._settings.OBJECT_CONFIG_PATH,
        )
        model_provider = ModelProvider(build_data.object_models + self._declared_models)
        object_routes = self._build_object_routes(build_data, model_provider)

    def _build_object_routes(self, build_data: BuildData, model_provider: ModelProvider) -> List[ConfiguiredFastapiEndpoint]:
        result: List[ConfiguiredFastapiEndpoint] = []
    
        for object_intermediate in build_data.object_intermediates:
            for endpoint_config in object_intermediate.api.endpoint_configs:
                if self._endpoint_builder_provider.has(endpoint_config.resolver_id)
                if endpoint_config.resolver_id not in self._endpoint_resolvers:
                    continue

                resolver: EndpointResolver = self._endpoint_resolvers[endpoint_config.resolver_id]
                endpoint: Endpoint = resolver.generate_endpoint(
                    self._service_container.models_resolver,
                    endpoint_config,
                    object_intermediate.api,
                )

        return result
