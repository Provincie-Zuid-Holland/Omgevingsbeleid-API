from typing import List, Optional

from app.dynamic.config.models import Model
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event.types import Listener


class InsertComputedFieldsListener(Listener[CreateModelEvent]):
    """
    CreateModelEvent listener used to manually add extra fields without a column.
    such as sqlalchemy hybrid properties or other computed values.

    example:

    - Add sqlachemy hybrid_property/attr to any sqlalchemy model
    - Register pyd response schema model id in extension setup
    - edit yaml file of an object and add service:
      insert_computed_fields:
        fields:
          - field_name: Public_Revisions
            model_id: public_module_object_revision
            list: true
            optional: true
    """

    SERVICE_NAME: str = "insert_computed_fields"

    def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        config: dict = service_config.get(self.SERVICE_NAME, None)
        if not config:
            return event

        fields_config: List[dict] = config.get("fields", None)

        for field in fields_config:
            field_name: str = field.get("field_name")
            model_id: str = field.get("model_id")
            is_optional: bool = field.get("optional", False)
            is_list: bool = field.get("list", False)

            model: Model = event.context.models_resolver.get(model_id)
            schema = model.pydantic_model
            if is_list:
                schema = List[schema]
            if is_optional:
                schema = Optional[schema]

            event.payload.pydantic_fields[field_name] = (schema, None)

        return event
