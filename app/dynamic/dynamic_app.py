from typing import Dict, List
from os import listdir
from os.path import isfile, join
from copy import deepcopy

import yaml
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse

from app.dynamic.db.objects_table import generate_dynamic_objects
from app.dynamic.db.object_static_table import generate_dynamic_object_statics
from app.dynamic.validators.validator import (
    HtmlValidator,
    LengthValidator,
    PlainTextValidator,
)

from .config.loader.models import ModelsLoader
from .config.loader.columns import columns_loader
from .config.loader.fields import fields_loader
from .config.loader.api import api_loader
from .config.models import Column, Field, IntermediateObject, Model
from .config.base_columns import base_columns
from .config.base_fields import base_fields
from app.dynamic.extension import Extension
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.service_container import ServiceContainer
import app.dynamic.serializers as serializers


class DynamicApp:
    def __init__(self, fastapi_app: FastAPI):
        self._fastapi_app: FastAPI = fastapi_app

    def run(self):
        print()
        print("in run")
        return self._fastapi_app


class DynamicAppBuilder:
    def __init__(self, main_config_file: str):
        # Data that is only needed for the build phase
        # Build should return a new service which can then be ran
        self._main_config: dict = self._load_yml(main_config_file)
        self._config_objects: List[dict] = []
        self._columns: Dict[str, Column] = {c.id: c for c in deepcopy(base_columns)}
        self._base_fields: Dict[str, Field] = {f.id: f for f in deepcopy(base_fields)}
        self._extensions: List[Extension] = []
        self._endpoint_resolvers: Dict[str, EndpointResolver] = {}
        self._service_container: ServiceContainer = ServiceContainer()

    def register_extension(self, extension: Extension):
        self._extensions.append(extension)

    def register_objects(self, dir_path: str):
        file_paths: List[str] = [
            join(dir_path, f)
            for f in listdir(dir_path)
            if isfile(join(dir_path, f))
            if f[0:1] != "_"
        ]
        for file_path in file_paths:
            self.register_object(file_path)

    def register_object(self, file_path: str):
        config = self._load_yml(file_path)
        self._config_objects.append(config)

    def build(self) -> DynamicApp:
        fastapi_app: FastAPI = FastAPI(
            title="Dynamic APP",
            openapi_url="/openapi.json",
        )
        main_router: APIRouter = APIRouter()

        self._register_base_serializers()
        self._register_base_validators()

        self._columns = columns_loader(
            self._columns, self._main_config.get("columns", {})
        )

        # Pre hook for extensions
        for extension in self._extensions:
            # extension.supply_service_container(self._service_container)
            extension.register_listeners(
                self._main_config,
                self._service_container.event_dispatcher,
                self._service_container.converter,
                self._service_container.models_resolver,
            )
            for column in extension.register_base_columns():
                self._columns[column.id] = column
            for base_field in extension.register_base_fields():
                self._base_fields[base_field.id] = base_field
            endpoint_resolvers: List[
                EndpointResolver
            ] = extension.register_endpoint_resolvers(
                self._service_container.event_dispatcher,
                self._service_container.converter,
                self._service_container.models_resolver,
            )
            self._merge_endpoint_resolvers(endpoint_resolvers)

        generate_dynamic_objects(self._columns)
        generate_dynamic_object_statics(self._columns)
        for extension in self._extensions:
            extension.register_tables(self._columns)

        # table_metadata.drop_all(engine)
        # table_metadata.create_all(engine)

        # Build extensions models
        for extension in self._extensions:
            extension.register_models(self._service_container.models_resolver)

        # Build config intermediate data (without models)
        for config_object in self._config_objects:
            self._build_config_intermediate(config_object)

        # Build data converters
        for object_intermediate in self._service_container.build_object_intermediates:
            self._service_container.converter.build_for_object(object_intermediate)

        # Build intermediate models
        models_loader: ModelsLoader = ModelsLoader(
            self._service_container.event_dispatcher,
            self._service_container.models_resolver,
            self._service_container.validator_provider,
        )
        for object_intermediate in self._service_container.build_object_intermediates:
            model_intermediates = models_loader.load_intermediates(object_intermediate)
            self._service_container.build_model_intermediates = (
                self._service_container.build_model_intermediates + model_intermediates
            )

        # Build the models without services / references
        # @todo: Should build models in order which is cleaner
        for model_intermediate in self._service_container.build_model_intermediates:
            if not model_intermediate.service_config:
                model: Model = models_loader.load_model(model_intermediate)
                self._service_container.models_resolver.add(model)
        # Build the models with services / references
        for model_intermediate in self._service_container.build_model_intermediates:
            if model_intermediate.service_config:
                model: Model = models_loader.load_model(model_intermediate)
                self._service_container.models_resolver.add(model)

        # Build api
        list.sort(
            self._service_container.build_object_intermediates,
            key=lambda o: o.id,
            reverse=False,
        )
        for object_intermediate in self._service_container.build_object_intermediates:
            fastapi_app: FastAPI = self._build_object_api(
                fastapi_app, object_intermediate
            )

        for extension in self._extensions:
            extension.register_endpoints(
                self._service_container.event_dispatcher,
                self._service_container.converter,
                self._service_container.models_resolver,
                main_router,
            )

        # Build the main api
        fastapi_app = self._build_main_api(fastapi_app)

        fastapi_app.include_router(main_router)
        fastapi_app.add_exception_handler(
            ValueError, self._value_error_exception_handler
        )

        return DynamicApp(
            fastapi_app=fastapi_app,
        )

    def _build_config_intermediate(self, config: dict):
        id = config.get("id")
        object_type = config.get("object_type")

        fields: Dict[str, Field] = fields_loader(
            self._base_fields, config.get("fields", {})
        )
        api = api_loader(id, object_type, config.get("api", {}))

        object_data = IntermediateObject(
            id=id,
            object_type=object_type,
            columns=self._columns,
            fields=fields,
            config=config,
            api=api,
        )

        self._service_container.build_object_intermediates.append(object_data)

    def _build_object_api(
        self, fastapi_app: FastAPI, object_intermediate: IntermediateObject
    ) -> FastAPI:
        sub_router: APIRouter = APIRouter()
        for endpoint_config in object_intermediate.api.endpoint_configs:
            if not endpoint_config.resolver_id in self._endpoint_resolvers:
                continue

            resolver: EndpointResolver = self._endpoint_resolvers[
                endpoint_config.resolver_id
            ]
            endpoint: Endpoint = resolver.generate_endpoint(
                self._service_container.event_dispatcher,
                self._service_container.converter,
                self._service_container.models_resolver,
                endpoint_config,
                object_intermediate.api,
            )
            endpoint.register(sub_router)

        fastapi_app.include_router(sub_router)

        return fastapi_app

    def _build_main_api(self, fastapi_app: FastAPI) -> FastAPI:
        sub_router: APIRouter = APIRouter()
        main_api_config = api_loader(
            "",
            "",
            self._main_config.get("api", {}),
        )

        for endpoint_config in main_api_config.endpoint_configs:
            if not endpoint_config.resolver_id in self._endpoint_resolvers:
                continue

            resolver: EndpointResolver = self._endpoint_resolvers[
                endpoint_config.resolver_id
            ]
            endpoint: Endpoint = resolver.generate_endpoint(
                self._service_container.event_dispatcher,
                self._service_container.converter,
                self._service_container.models_resolver,
                endpoint_config,
                main_api_config,
            )
            endpoint.register(sub_router)

        fastapi_app.include_router(sub_router)

        return fastapi_app

    def _load_yml(self, file_path: str) -> dict:
        with open(file_path) as stream:
            return yaml.safe_load(stream)

    def _register_base_serializers(self):
        self._service_container.converter.register_serializer(
            "str", serializers.serializer_str
        )
        self._service_container.converter.register_serializer(
            "optional_str", serializers.serializer_optional_str
        )
        self._service_container.converter.register_serializer(
            "uuid", serializers.serializer_uuid
        )
        self._service_container.converter.register_serializer(
            "optional_uuid", serializers.serializer_optional_uuid
        )

    def _register_base_validators(self):
        self._service_container.validator_provider.register(LengthValidator())
        self._service_container.validator_provider.register(PlainTextValidator())
        self._service_container.validator_provider.register(HtmlValidator())

    def _merge_endpoint_resolvers(self, resolvers: List[EndpointResolver]):
        for resolver in resolvers:
            resolver_id = resolver.get_id()
            if resolver_id in self._endpoint_resolvers:
                raise RuntimeError(
                    f"Trying to add already existsing resolver ID '{resolver_id}'"
                )
            self._endpoint_resolvers[resolver_id] = resolver

    @staticmethod
    def _value_error_exception_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )