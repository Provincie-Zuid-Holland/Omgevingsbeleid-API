from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.endpoint import EndpointContextBuilderData
from app.build.api_models import DECLARED_MODELS
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.endpoint_builders.endpoint_builder_provider import EndpointBuilderProvider
from app.build.objects.types import BuildData, EndpointConfig, ObjectApi
from app.build.services.config_parser import ConfigParser
from app.build.services.object_models_builder import ObjectModelsBuilder
from app.build.services.tables_builder import TablesBuilder
from app.core.services.models_provider import ModelsProvider
from app.core.services.object_field_mapping_provider import ObjectFieldMappingProvider


@dataclass
class ApiBuilderResult:
    object_field_mapping_provider: ObjectFieldMappingProvider
    routes: List[ConfiguredFastapiEndpoint]
    required_object_fields_rule_mapping: Dict[str, Type[BaseModel]]
    publication_required_object_fields_rule_mapping: Dict[str, Dict[str, Type[BaseModel]]]


class ApiBuilder:
    def __init__(
        self,
        config_parser: ConfigParser,
        object_models_builder: ObjectModelsBuilder,
        tables_builder: TablesBuilder,
        endpoint_builder_provider: EndpointBuilderProvider,
        models_provider: ModelsProvider,
    ):
        self._config_parser: ConfigParser = config_parser
        self._object_models_builder: ObjectModelsBuilder = object_models_builder
        self._tables_builder: TablesBuilder = tables_builder
        self._endpoint_builder_provider: EndpointBuilderProvider = endpoint_builder_provider
        self._models_provider: ModelsProvider = models_provider

    def build(self, session: Session) -> ApiBuilderResult:
        build_data: BuildData = self._config_parser.parse()

        self._tables_builder.build_tables(session, build_data.columns)

        self._models_provider.add_list(DECLARED_MODELS)
        self._object_models_builder.build_models(session, self._models_provider, build_data.object_intermediates)

        object_field_mapping_provider: ObjectFieldMappingProvider = self._build_object_field_mapping_provider(
            build_data
        )

        object_routes: List[ConfiguredFastapiEndpoint] = self._build_object_routes(build_data)
        object_routes = object_routes + self._build_main_routes(build_data)
        object_routes.sort(key=lambda o: o.tags)

        required_object_fields_rule_mapping: Dict[str, Type[BaseModel]] = self._build_object_fields_rule_mapping(
            build_data,
            self._models_provider,
        )

        publication_required_object_fields_rule_mapping: Dict[str, Dict[str, Type[BaseModel]]] = (
            self._build_publication_object_fields_rule_mapping(
                build_data,
                self._models_provider,
            )
        )

        return ApiBuilderResult(
            object_field_mapping_provider=object_field_mapping_provider,
            routes=object_routes,
            required_object_fields_rule_mapping=required_object_fields_rule_mapping,
            publication_required_object_fields_rule_mapping=publication_required_object_fields_rule_mapping,
        )

    def _build_object_fields_rule_mapping(
        self,
        build_data: BuildData,
        models_provider: ModelsProvider,
    ) -> Dict[str, Type[BaseModel]]:
        rule_mapping: Dict[str, Type[BaseModel]] = {}
        rule_config: Dict[str, str] = build_data.main_config["required_object_fields_rule"]
        for object_type, model_name in rule_config.items():
            model_type: Type[BaseModel] = models_provider.get_pydantic_model(model_name)
            rule_mapping[object_type] = model_type
        return rule_mapping

    def _build_publication_object_fields_rule_mapping(
        self,
        build_data: BuildData,
        models_provider: ModelsProvider,
    ) -> Dict[str, Dict[str, Type[BaseModel]]]:
        rule_mapping: Dict[str, Dict[str, Type[BaseModel]]] = {}
        rule_config: Dict[Dict[str, str]] = build_data.main_config["publication_required_object_fields_rule"]
        for publication_type, object_and_model in rule_config.items():
            for object_type, model_name in object_and_model.items():
                model_type: Type[BaseModel] = models_provider.get_pydantic_model(model_name)
                object_type_data = {}
                if publication_type in rule_mapping:
                    object_type_data = rule_mapping[publication_type]
                object_type_data[object_type] = model_type
                rule_mapping[publication_type] = object_type_data
        return rule_mapping

    def _build_object_field_mapping_provider(self, build_data: BuildData) -> ObjectFieldMappingProvider:
        object_field_mappings: Dict[str, Set[str]] = {}
        for object_intermediate in build_data.object_intermediates:
            field_names: Set[str] = {field.name for field in object_intermediate.fields.values()}
            object_field_mappings[object_intermediate.object_type] = field_names
        return ObjectFieldMappingProvider(object_field_mappings)

    def _build_object_routes(self, build_data: BuildData) -> List[ConfiguredFastapiEndpoint]:
        result: List[ConfiguredFastapiEndpoint] = []

        for object_intermediate in build_data.object_intermediates:
            for endpoint_config in object_intermediate.api.endpoint_configs:
                endpoint_builder: Optional[EndpointBuilder] = self._endpoint_builder_provider.get_optional(
                    endpoint_config.resolver_id
                )
                if endpoint_builder is None:
                    raise ValueError(f"EndpointBuilder with id '{endpoint_config.resolver_id}' does not exist.")

                # Convenience which happens in every endpoint builder
                resolver_config: dict = endpoint_config.resolver_data
                path: str = endpoint_config.prefix + resolver_config.get("path", "")
                builder_data: EndpointContextBuilderData = EndpointContextBuilderData(
                    endpoint_id=endpoint_config.resolver_id,
                    path=path,
                )

                configured_endpoint: ConfiguredFastapiEndpoint = endpoint_builder.build_endpoint(
                    self._models_provider,
                    builder_data,
                    endpoint_config,
                    object_intermediate.api,
                )
                result.append(configured_endpoint)

        return result

    def _build_main_routes(self, build_data: BuildData) -> List[ConfiguredFastapiEndpoint]:
        result: List[ConfiguredFastapiEndpoint] = []

        main_endpoint_configs: List[EndpointConfig] = self._parse_main_api_endpoint_configs(
            build_data.main_config.get("api", {})
        )
        # @todo: Its a bit weird that its called Object here
        # And object_id and object_type are not needed
        api = ObjectApi(
            object_id="",
            object_type="",
            endpoint_configs=main_endpoint_configs,
        )

        for endpoint_config in main_endpoint_configs:
            endpoint_builder: Optional[EndpointBuilder] = self._endpoint_builder_provider.get_optional(
                endpoint_config.resolver_id
            )
            if endpoint_builder is None:
                raise ValueError(f"EndpointBuilder with id '{endpoint_config.resolver_id}' does not exist.")

            # Convenience which happens in every endpoint builder
            resolver_config: dict = endpoint_config.resolver_data
            path: str = endpoint_config.prefix + resolver_config.get("path", "")
            builder_data: EndpointContextBuilderData = EndpointContextBuilderData(
                endpoint_id=endpoint_config.resolver_id,
                path=path,
            )

            configured_endpoint: ConfiguredFastapiEndpoint = endpoint_builder.build_endpoint(
                self._models_provider,
                builder_data,
                endpoint_config,
                api,
            )
            result.append(configured_endpoint)

        return result

    def _parse_main_api_endpoint_configs(self, api_config: dict) -> List[EndpointConfig]:
        endpoints: List[EndpointConfig] = []

        for router_config in api_config.get("routers", []):
            prefix: str = router_config.get("prefix", "")

            for endpoint_config in router_config.get("endpoints", []):
                resolver_id: str = endpoint_config.get("resolver")
                resolver_data: dict = endpoint_config.get("resolver_data", {})
                endpoints.append(
                    EndpointConfig(
                        prefix=prefix,
                        resolver_id=resolver_id,
                        resolver_data=resolver_data,
                    )
                )

        return endpoints
