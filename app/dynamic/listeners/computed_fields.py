from typing import List, Optional
from pydantic import Field

from app.dynamic.computed_field_resolver import ComputedFieldResolver
from app.dynamic.config.models import ComputedField, Model
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event.types import Listener


class ComputedFieldsListener(Listener[CreateModelEvent]):
    """
    CreateModelEvent listener used to manually add extra fields without a column.
    such as sqlalchemy hybrid properties or other computed values.

    example:

    - Add sqlachemy hybrid_property/attr to any sqlalchemy model
    - Register pyd response schema model id in extension setup
    """

    SERVICE_NAME: str = "computed_fields"

    def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        computed_fields: List[str] = service_config.get(self.SERVICE_NAME, None)
        if not computed_fields:
            return event

        computed_fields_resolver: ComputedFieldResolver = event.context.computed_fields_resolver
        for computed_field_id in computed_fields:
            # TODO: catch runtime error if computed field not found
            computed_field: ComputedField = computed_fields_resolver.get(computed_field_id)
            if computed_field.static != event.context.intermediate_model.static_only:
                continue

            model: Model = event.context.models_resolver.get(computed_field.model_id)
            schema = model.pydantic_model
            if computed_field.is_list:
                schema = List[schema]
            if computed_field.is_optional:
                schema = Optional[schema]

            event.payload.pydantic_fields[computed_field.attribute_name] = (
                schema,
                Field(
                    **{
                        "default": None,
                        "nullable": computed_field.is_optional,
                    }
                ),
            )

        return event


    # def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
    #     service_config: dict = event.context.intermediate_model.service_config
    #     config: dict = service_config.get(self.SERVICE_NAME, None)
    #     if not config:
    #         return event

    #     fields_config: List[dict] = config.get("fields", None)

    #     for field in fields_config:
    #         field_name: str = field.get("field_name")
    #         model_id: str = field.get("model_id")
    #         is_optional: bool = field.get("optional", False)
    #         is_list: bool = field.get("list", False)

    #         model: Model = event.context.models_resolver.get(model_id)
    #         schema = model.pydantic_model
    #         if is_list:
    #             schema = List[schema]
    #         if is_optional:
    #             schema = Optional[schema]

    #         event.payload.pydantic_fields[field_name] = (schema, None)

    #     return event
