from typing import List, Optional
from sqlalchemy.orm import Session

from app.api.endpoint import EndpointContextBuilderData
from app.build.api_models import DECLARED_MODELS
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.endpoint_builders.endpoint_builder_provider import EndpointBuilderProvider
from app.build.objects.types import BuildData
from app.build.services.config_parser import ConfigParser
from app.build.services.object_models_builder import ObjectModelsBuilder
from app.build.services.tables_builder import TablesBuilder
from app.core.services.models_provider import ModelsProvider
from app.core.settings import Settings


class ApiBuilder:
    def __init__(
        self,
        db: Session,
        config_parser: ConfigParser,
        object_models_builder: ObjectModelsBuilder,
        tables_builder: TablesBuilder,
        endpoint_builder_provider: EndpointBuilderProvider,
        models_provider: ModelsProvider,
    ):
        self._db: Session = db
        self._config_parser: ConfigParser = config_parser
        self._object_models_builder: ObjectModelsBuilder = object_models_builder
        self._tables_builder: TablesBuilder = tables_builder
        self._endpoint_builder_provider: EndpointBuilderProvider = endpoint_builder_provider
        self._models_provider: ModelsProvider = models_provider

    def build(self) -> List[ConfiguiredFastapiEndpoint]:
        build_data: BuildData = self._config_parser.parse()

        self._tables_builder.build_tables(build_data.columns)
        
        self._models_provider.add_list(DECLARED_MODELS)
        self._object_models_builder.build_models(self._models_provider, build_data.object_intermediates)

        object_routes: List[ConfiguiredFastapiEndpoint] = self._build_object_routes(build_data)
        return object_routes

    def _build_object_routes(self, build_data: BuildData) -> List[ConfiguiredFastapiEndpoint]:
        result: List[ConfiguiredFastapiEndpoint] = []
    
        for object_intermediate in build_data.object_intermediates:
            for endpoint_config in object_intermediate.api.endpoint_configs:
                endpoint_builder: Optional[EndpointBuilder] = self._endpoint_builder_provider.get_optional(
                    endpoint_config.resolver_id
                )
                if endpoint_builder is None:
                    continue
                    # @todo:
                    # raise ValueError(f"EndpointBuilder with id '{endpoint_config.resolver_id}' does not exist.")

                # Convience which happens in every endpoint builder
                resolver_config: dict = endpoint_config.resolver_data
                path: str = endpoint_config.prefix + resolver_config.get("path", "")
                builder_data: EndpointContextBuilderData = EndpointContextBuilderData(
                    endpoint_id=endpoint_config.resolver_id,
                    path=path,
                )

                configured_endpoint: ConfiguiredFastapiEndpoint = endpoint_builder.build_endpoint(
                    self._models_provider,
                    builder_data,
                    endpoint_config,
                    object_intermediate.api,
                )
                result.append(configured_endpoint)

        return result
