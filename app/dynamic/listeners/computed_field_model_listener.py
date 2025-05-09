from typing import List, Optional

from pydantic import Field

from app.dynamic.computed_fields import ComputedField, ComputedFieldResolver
from app.dynamic.config.models import Model
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event.types import Listener


class ComputedFieldModelListener(Listener[CreateModelEvent]):
    SERVICE_NAME: str = "computed_fields"

    def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        computed_fields_config = service_config.get(self.SERVICE_NAME, None)
        if not computed_fields_config:
            return event

        computed_fields_resolver: ComputedFieldResolver = event.context.computed_fields_resolver

        # add each computed field to the pydantic model
        for computed_field_id in computed_fields_config:
            computed_field: ComputedField = computed_fields_resolver.get(computed_field_id)
            model: Model = event.context.models_resolver.get(computed_field.model_id)

            schema = model.pydantic_model
            if computed_field.is_list:
                schema = List[schema]
            if computed_field.is_optional:
                schema = Optional[schema]

            event.payload.pydantic_fields[computed_field.attribute_name] = (
                schema,
                Field(
                    default=None,
                    validation_alias=computed_field.attribute_name,
                ),
            )

        return event
