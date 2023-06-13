from typing import Callable, List, Dict, Any, Optional, Tuple
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
        self._root_validator_counter: int = 0

        # @todo: should be injected so that extensions can also register default values
        self._defaults: Dict[str, Any] = {
            "none": None,
        }

    def load_intermediates(
        self, object_intermediate: IntermediateObject
    ) -> List[IntermediateModel]:
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

            root_validators_config: List[dict] = model_config.get("root_validators", [])
            root_validators: Dict[str, Callable] = self._get_root_validators(
                root_validators_config
            )

            models.append(
                IntermediateModel(
                    id=model_id,
                    name=name,
                    static_only=static_only,
                    columns=columns,
                    fields=fields,
                    static_fields=static_fields,
                    service_config=model_config.get("services", {}),
                    root_validators=root_validators,
                )
            )

        return models

    def load_model(self, intermediate_model: IntermediateModel) -> DynamicObjectModel:
        # If we requested a static object and we have lineage fields then we have a configuration error
        if intermediate_model.static_only and intermediate_model.fields:
            raise RuntimeError(
                f"Can not configure lineage fields for static only model '{intermediate_model.name}"
            )
        if intermediate_model.static_only and not intermediate_model.static_fields:
            raise RuntimeError(
                f"Must configure static fields for static only model '{intermediate_model.name}"
            )

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
            )
        )
        pydantic_fields = event.payload.pydantic_fields
        static_pydantic_fields = event.payload.static_pydantic_fields

        # If we have static fields then we need to make a static wrapper object
        if static_pydantic_fields:
            # If this will be the outer model than we need to merge the root validators
            if intermediate_model.static_only:
                static_pydantic_validators = (
                    static_pydantic_validators | intermediate_model.root_validators
                )

            static_object_name = f"{intermediate_model.name}Statics"
            pydantic_static_model = pydantic.create_model(
                static_object_name,
                __config__=DynamicModelPydanticConfig,
                __validators__=static_pydantic_validators,
                **static_pydantic_fields,
            )
            # Attach the Statics Model to the main model
            # @note: the name is hardcoded to 'ObjectStatics'
            #           because that is the same name in the sqlalchemy ObjectsTable
            pydantic_fields["ObjectStatics"] = (
                pydantic_static_model,
                pydantic.Field(
                    **{
                        "default": None,
                        "nullable": True,
                    }
                ),
            )

        # If we have a static_only model then we use the "ObjectStatics" as the main model
        if intermediate_model.static_only:
            pydantic_model = pydantic_static_model
        else:
            pydantic_model = pydantic.create_model(
                intermediate_model.name,
                __config__=DynamicModelPydanticConfig,
                __validators__=(
                    pydantic_validators | intermediate_model.root_validators
                ),
                **pydantic_fields,
            )

        return DynamicObjectModel(
            id=intermediate_model.id,
            name=intermediate_model.name,
            pydantic_model=pydantic_model,
            service_config=intermediate_model.service_config,
            columns=[],
        )

    def _get_pydantic_fields(
        self, fields: List[Field], validator_prefix: str
    ) -> Tuple[OrderedDict, dict]:
        pydantic_fields = OrderedDict()
        pydantic_validators = {}

        for field in fields:
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
                    f"{validator_prefix}-{len(pydantic_validators) + 1}"
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
                    }
                ),
            )

        return pydantic_fields, pydantic_validators

    def _get_root_validators(self, config) -> Dict[str, Callable]:
        if not config:
            return {}

        root_validators: Dict[str, Callable] = {}
        for validator_config in config:
            validator_id: str = validator_config.get("id", "")
            validator_data: dict = validator_config.get("data", {})
            validator_func = self._validator_provider.get_validator(
                validator_id, validator_data
            )

            self._root_validator_counter += 1
            unique_name: str = f"root_validator_{self._root_validator_counter}"

            # fmt: off
            pydantic_validator_func = pydantic.root_validator(allow_reuse=True)(validator_func)
            root_validators[unique_name] = pydantic_validator_func
            # fmt: on

        return root_validators
