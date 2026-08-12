from collections.abc import Callable
from copy import deepcopy
from typing import Any

import pydantic

from app.build.objects.fields import BASE_FIELDS, FIELD_TYPES
from app.build.objects.types import EndpointConfig, Field, IntermediateModel, IntermediateObject, ObjectApi
from app.build.services.validator_provider import ValidatorProvider
from app.core.types import Column


class ObjectIntermediateBuilder:
    def __init__(self, validator_provider: ValidatorProvider):
        self._validator_provider: ValidatorProvider = validator_provider

    def build(self, columns: dict[str, Column], config_objects: list[dict]) -> list[IntermediateObject]:
        result: list[IntermediateObject] = []

        for object_config in config_objects:
            object_id: str = object_config["id"]
            object_type: str = object_config["object_type"]

            fields: dict[str, Field] = self._load_object_fields(object_config.get("fields", {}))
            api: ObjectApi = self._load_object_api(object_id, object_type, object_config.get("api", {}))

            intermediate_models: list[IntermediateModel] = self._build_intermediate_models_per_object(
                columns,
                fields,
                object_config.get("models", {}),
            )

            object_data = IntermediateObject(
                id=object_id,
                object_type=object_type,
                fields=fields,
                config=object_config,
                api=api,
                intermediate_models=intermediate_models,
            )
            result.append(object_data)

        return result

    def _load_object_fields(self, config: dict) -> dict[str, Field]:
        fields: dict[str, Field] = {f.id: f for f in deepcopy(BASE_FIELDS)}

        for field_id, data in config.items():
            if field_id in fields:
                raise RuntimeError(f"Field ID: '{field_id}' already exists")

            default_value = FIELD_TYPES[data.get("type")].default
            if "default" in data:
                default_value = data.get("default")

            fields[field_id] = Field(
                id=field_id,
                column=data["column"],
                name=data["name"],
                type=data["type"],
                optional=data.get("optional", False),
                validators=data.get("validators", []),
                formatters=data.get("formatters", []),
                default=default_value,
            )

        return fields

    def _load_object_api(self, object_id: str, object_type: str, api_config: dict) -> ObjectApi:
        endpoints: list[EndpointConfig] = []

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

        return ObjectApi(
            object_id=object_id,
            object_type=object_type,
            endpoint_configs=endpoints,
        )

    def _build_intermediate_models_per_object(
        self,
        all_columns: dict[str, Column],
        all_fields: dict[str, Field],
        models_config: dict[str, dict[str, Any]],
    ) -> list[IntermediateModel]:
        result: list[IntermediateModel] = []

        for model_id, model_config in models_config.items():
            name: str = model_config["name"]
            static_only: bool = model_config.get("static_only", False)
            model_columns: list[Column] = []
            fields: list[Field] = []
            static_fields: list[Field] = []

            for field_id, overwrites in model_config.get("fields", {}).items():
                field = deepcopy(all_fields[field_id])
                field.overwrite(overwrites)

                column = all_columns[field.column]
                if column.static:
                    static_fields.append(field)
                else:
                    fields.append(field)

                model_columns.append(column)

            model_validators_config: list[dict] = model_config.get("model_validators", [])
            model_validators: dict[str, Callable] = self._build_model_validators(model_validators_config)

            result.append(
                IntermediateModel(
                    id=model_id,
                    name=name,
                    static_only=static_only,
                    columns=model_columns,
                    fields=fields,
                    static_fields=static_fields,
                    service_config=model_config.get("services", {}),
                    model_validators=model_validators,
                    dependency_model_ids=model_config.get("dependency_model_ids", []),
                )
            )

        return result

    def _build_model_validators(self, model_validators_config: list[dict]) -> dict[str, Callable]:
        result: dict[str, Callable] = {}

        for validator_config in model_validators_config:
            validator_id: str = validator_config["id"]
            validator_data: dict = validator_config.get("data", {})
            validator_unique_counter, validator_func = self._validator_provider.get(validator_id, validator_data)

            unique_name: str = f"model_validator_{validator_unique_counter}"

            pydantic_validator_func = pydantic.model_validator(mode=validator_func.mode)(validator_func.func)  # type: ignore
            result[unique_name] = pydantic_validator_func

        return result
