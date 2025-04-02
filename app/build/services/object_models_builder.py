
from graphlib import TopologicalSorter
from typing import Any, Dict, List, Optional, OrderedDict, Tuple

import pydantic

from app.build.objects.fields import FIELD_TYPES
from app.build.objects.types import Field, IntermediateModel, IntermediateObject
from app.build.services.validator_provider import ValidatorProvider
from app.core.models_provider import ModelsProvider
from app.core.types import Model, DynamicObjectModel


class ObjectModelsBuilder:
    def __init__(self, validator_provider: ValidatorProvider):
        self._validator_provider: ValidatorProvider = validator_provider

        self._field_defaults: Dict[str, Any] = {
            "none": None,
        }

    def build_models(
            self,
            models_provider: ModelsProvider,
            intermediate_objects: List[IntermediateObject],
        ):
        intermediate_models: List[IntermediateModel] = [
            i_model for i_object in intermediate_objects
            for i_model in i_object.intermediate_models
        ]
        intermediate_models = self._sort_intermediate_objects(intermediate_models)

        for intermediate_model in intermediate_models:
            model: Model = self._build_model(intermediate_model)
            models_provider.add(model)

    def _sort_intermediate_objects(self, intermediate_objects: List[IntermediateModel]) -> List[IntermediateModel]:
        """
        Sorts intermediate objects based on their dependencies using topological sort.
        Ensures each object appears after its dependencies.
        """
        intermediate_objects_lookup = {o.id: o for o in intermediate_objects}
        
        dependency_map = {}
        for int_obj in intermediate_objects:
            dependency_map[int_obj.id] = {
                dep_id for dep_id in int_obj.dependency_model_ids
                if dep_id in intermediate_objects_lookup
            }
        
        ts = TopologicalSorter(dependency_map)
        sorted_model_ids = list(ts.static_order())

        sorted_models: List[IntermediateModel] = [
            intermediate_objects_lookup[model_id] for model_id in sorted_model_ids
        ]

        return sorted_models

    def _build_model(self, intermediate_model: IntermediateModel) -> DynamicObjectModel:
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
        # @TODO: Executre those listeners
        # event: CreateModelEvent = self._event_dispatcher.dispatch(
        #     CreateModelEvent.create(
        #         pydantic_fields,
        #         static_pydantic_fields,
        #         intermediate_model,
        #         self._models_resolver,
        #         self._computed_fields_resolver,
        #     )
        # )
        # pydantic_fields = event.payload.pydantic_fields
        # static_pydantic_fields = event.payload.static_pydantic_fields

        # If we have static fields then we need to make a static wrapper object
        if static_pydantic_fields:
            # If this will be the outer model than we need to merge the root validators
            if intermediate_model.static_only:
                static_pydantic_validators = {**pydantic_validators, **intermediate_model.model_validators}

            static_object_name = f"{intermediate_model.name}Statics"
            pydantic_static_model = pydantic.create_model(
                static_object_name,
                __config__=pydantic.ConfigDict(from_attributes=True),
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
            pydantic_model = pydantic_static_model # type: ignore
        else:
            pydantic_model = pydantic.create_model(
                intermediate_model.name,
                __config__=pydantic.ConfigDict(from_attributes=True),
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
            if field_type in FIELD_TYPES:
                field_type = FIELD_TYPES[field_type].field_type

            if field.optional:
                field_type = Optional[field_type]

            default_value = field.default
            if default_value in self._field_defaults:
                default_value = self._field_defaults[default_value]

            for validator_config in field.validators:
                validator_id: str = validator_config.get("id", "")
                validator_data: dict = validator_config.get("data", {})
                unique_counter, validator_func = self._validator_provider.get(validator_id, validator_data)

                pydantic_validator_unique_name: str = f"{validator_prefix}-{unique_counter}"
                pydantic_validator_func = pydantic.field_validator(field.name, mode=validator_func.mode)(validator_func.func)
                pydantic_validators[pydantic_validator_unique_name] = pydantic_validator_func

            pydantic_fields[field.name] = (
                field_type,
                pydantic.Field(
                    default=default_value,
                ),
            )

        return pydantic_fields, pydantic_validators
