from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple

import pydantic

from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.validators.validator_provider import ValidatorProvider

from ..models import DynamicObjectModel, Field, IntermediateModel, IntermediateObject
from .fields import field_types


class ModelsLoader:
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        models_resolver: ModelsResolver,
        computed_fields_resolver: ComputedFieldResolver,
        validator_provider: ValidatorProvider,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._models_resolver: ModelsResolver = models_resolver
        self._computed_fields_resolver: ComputedFieldResolver = computed_fields_resolver
        self._validator_provider: ValidatorProvider = validator_provider
        self._model_validator_counter: int = 0

        # @todo: should be injected so that extensions can also register default values
        self._defaults: Dict[str, Any] = {
            "none": None,
        }

    def load_intermediates(self, object_intermediate: IntermediateObject) -> List[IntermediateModel]:
        models: List[IntermediateModel] = []

        model_configs: dict = object_intermediate.config.get("models", {})
        for model_id, model_config in model_configs.items():
            name: str = model_config.get("name")
            static_only: bool = model_config.get("static_only", False)
            columns: List[str] = []
            fields: List[Field] = []
            static_fields: List[Field] = []

            for field_id, overwrites in model_config.get("fields", {}).items():
                field = deepcopy(object_intermediate.fields[field_id])
                field.overwrite(overwrites)

                # Check if the column exists and where this field belongs
                column = object_intermediate.columns.get(field.column, None)
                if not column:
                    raise RuntimeError(
                        f"Column '{field.column}' does not exists. It is used by field '{field.name}' in model '{name}'"
                    )

                if column.static:
                    static_fields.append(field)
                else:
                    fields.append(field)

                columns.append(field.column)

            model_validators_config: List[dict] = model_config.get("model_validators", [])
            model_validators: Dict[str, Callable] = self._get_model_validators(model_validators_config)

            models.append(
                IntermediateModel(
                    id=model_id,
                    name=name,
                    static_only=static_only,
                    columns=columns,
                    fields=fields,
                    static_fields=static_fields,
                    service_config=model_config.get("services", {}),
                    model_validators=model_validators,
                )
            )

        return models

    def load_model(self, intermediate_model: IntermediateModel) -> DynamicObjectModel:
        # If we requested a static object and we have lineage fields then we have a configuration error
        if intermediate_model.static_only and intermediate_model.fields:
            raise RuntimeError(f"Can not configure lineage fields for static only model '{intermediate_model.name}")
        if intermediate_model.static_only and not intermediate_model.static_fields:
            raise RuntimeError(f"Must configure static fields for static only model '{intermediate_model.name}")

        pydantic_fields, pydantic_validators = self._get_pydantic_fields(
            intermediate_model.fields,
            f"{intermediate_model.name}-dynamic",
        )
        static_pydantic_fields, static_pydantic_validators = self._get_pydantic_fields(
            intermediate_model.static_fields,
            f"{intermediate_model.name}-static",
        )

        # Ask extensions for more information
        event: CreateModelEvent = self._event_dispatcher.dispatch(
            CreateModelEvent.create(
                pydantic_fields,
                static_pydantic_fields,
                intermediate_model,
                self._models_resolver,
                self._computed_fields_resolver,
            )
        )
        pydantic_fields = event.payload.pydantic_fields
        static_pydantic_fields = event.payload.static_pydantic_fields

        # If we have static fields then we need to make a static wrapper object
        if static_pydantic_fields:
            # If this will be the outer model than we need to merge the root validators
            if intermediate_model.static_only:
                static_pydantic_validators = {**pydantic_validators, **intermediate_model.model_validators}

            static_object_name = f"{intermediate_model.name}Statics"
            pydantic_static_model = pydantic.create_model(
                static_object_name,
                model_config=pydantic.ConfigDict(from_attributes=True),
                __validators__=static_pydantic_validators,
                **static_pydantic_fields,
            )
            # Attach the Statics Model to the main model
            # @note: the name is hardcoded to 'ObjectStatics'
            #           because that is the same name in the sqlalchemy ObjectsTable
            pydantic_fields["ObjectStatics"] = (
                pydantic_static_model,
                pydantic.Field(
                    default=None,
                ),
            )

        # If we have a static_only model then we use the "ObjectStatics" as the main model
        if intermediate_model.static_only:
            pydantic_model = pydantic_static_model
        else:
            pydantic_model = pydantic.create_model(
                intermediate_model.name,
                model_config=pydantic.ConfigDict(from_attributes=True),
                __validators__={**pydantic_validators, **intermediate_model.model_validators},
                **pydantic_fields,
            )

        return DynamicObjectModel(
            id=intermediate_model.id,
            name=intermediate_model.name,
            pydantic_model=pydantic_model,
            service_config=intermediate_model.service_config,
            columns=[],
        )

    def _get_pydantic_fields(self, fields: List[Field], validator_prefix: str) -> Tuple[OrderedDict, dict]:
        pydantic_fields = OrderedDict()
        pydantic_validators = {}

        for field in fields:
            field_type = field.type
            if field_type in field_types:
                field_type = field_types[field_type].field_type

            if field.optional:
                field_type = Optional[field_type]

            default_value = field.default
            if default_value in self._defaults:
                default_value = self._defaults[default_value]

            for validator_config in field.validators:
                validator_id: str = validator_config.get("id", "")
                validator_data: dict = validator_config.get("data", {})
                validator_func = self._validator_provider.get_validator(validator_id, validator_data)

                pydantic_validator_unique_name: str = f"{validator_prefix}-{len(pydantic_validators) + 1}"
                # fmt: off
                pydantic_validator_func = pydantic.field_validator(field.name, mode=validator_func.mode)(validator_func.func)
                pydantic_validators[pydantic_validator_unique_name] = pydantic_validator_func
                # fmt: on

            pydantic_fields[field.name] = (
                field_type,
                pydantic.Field(
                    default=default_value,
                ),
            )

        return pydantic_fields, pydantic_validators

    def _get_model_validators(self, config) -> Dict[str, Callable]:
        if not config:
            return {}

        model_validators: Dict[str, Any] = {}
        for validator_config in config:
            validator_id: str = validator_config.get("id", "")
            validator_data: dict = validator_config.get("data", {})
            validator_func = self._validator_provider.get_validator(validator_id, validator_data)

            self._model_validator_counter += 1
            unique_name: str = f"model_validator_{self._model_validator_counter}"

            pydantic_validator_func = pydantic.model_validator(mode=validator_func.mode)(validator_func.func)
            model_validators[unique_name] = pydantic_validator_func

        return model_validators
