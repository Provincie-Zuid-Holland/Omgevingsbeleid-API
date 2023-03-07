from typing import List, Dict, Any, Optional
from copy import deepcopy
from collections import OrderedDict

import pydantic

from app.dynamic.validators.validator_provider import ValidatorProvider

from ..models import IntermediateModel, IntermediateObject, Field, DynamicObjectModel
from .fields import field_types
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event.create_model_event import CreateModelEvent


class DynamicModelPydanticConfig:
    orm_mode: bool = True


class ModelsLoader:
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        models_resolver: ModelsResolver,
        validator_provider: ValidatorProvider,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._models_resolver: ModelsResolver = models_resolver
        self._validator_provider: ValidatorProvider = validator_provider

        # @todo: should be injected so that extensions can also register default values
        self._defaults: Dict[str, Any] = {
            "none": None,
        }

    def load_intermediates(
        self, object_intermediate: IntermediateObject
    ) -> List[IntermediateModel]:
        models: List[IntermediateModel] = []

        for model_id, model_config in object_intermediate.config.get(
            "models", {}
        ).items():
            name: str = model_config.get("name")
            columns: List[str] = []
            fields: List[Field] = []

            for field_id, overwrites in model_config.get("fields", {}).items():
                field = deepcopy(object_intermediate.fields[field_id])
                field.overwrite(overwrites)
                fields.append(field)

                columns.append(field.column)

            models.append(
                IntermediateModel(
                    id=model_id,
                    name=name,
                    columns=columns,
                    fields=fields,
                    service_config=model_config.get("services", {}),
                )
            )

        return models

    def load_model(self, intermediate_model: IntermediateModel) -> DynamicObjectModel:
        pydantic_fields = OrderedDict()
        pydantic_validators = {}

        for field in intermediate_model.fields:
            field_type = field.type
            if field_type in field_types:
                field_type = field_types[field_type]

            if field.optional:
                field_type = Optional[field_type]

            default_value = field.default
            if default_value in self._defaults:
                default_value = self._defaults[default_value]

            for validator_config in field.validators:
                validator_id: str = validator_config.get("id", "")
                validator_data: dict = validator_config.get("data", {})
                validator_func = self._validator_provider.get_validator(
                    validator_id, validator_data
                )

                pydantic_validator_unique_name: str = (
                    f"{intermediate_model.name}-{len(pydantic_validators) + 1}"
                )
                # fmt: off
                pydantic_validator_func = pydantic.validator(field.name, allow_reuse=True)(validator_func)
                pydantic_validators[pydantic_validator_unique_name] = pydantic_validator_func
                # fmt: on

                """
                Showing what is needed to register pydantic validators:
                __validators__={
                    "unique-name-1": pydantic.validator("Title", allow_reuse=True)(our_validator_func({
                        "min": 5,
                    })),
                    "unique-name-2": pydantic.validator("Description", allow_reuse=True)(our_validator_func({
                        "min": 6,
                    }))
                }
                """

            pydantic_fields[field.name] = (
                field_type,
                pydantic.Field(
                    **{
                        "default": default_value,
                        "nullable": field.optional,
                        "description": "description is not yet inherited",
                    }
                ),
            )

        # Ask extensions for more information
        event: CreateModelEvent = self._event_dispatcher.dispatch(
            CreateModelEvent.create(
                pydantic_fields,
                intermediate_model,
                self._models_resolver,
            )
        )
        pydantic_fields = event.payload.pydantic_fields

        pydantic_model = pydantic.create_model(
            intermediate_model.name,
            __config__=DynamicModelPydanticConfig,
            __validators__=pydantic_validators,
            **pydantic_fields,
        )

        return DynamicObjectModel(
            id=intermediate_model.id,
            name=intermediate_model.name,
            pydantic_model=pydantic_model,
            service_config=intermediate_model.service_config,
            columns=[],
        )
