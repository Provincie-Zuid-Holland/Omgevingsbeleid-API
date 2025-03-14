from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
from app.dynamic.computed_fields.handler_context import ComputedFieldHandlerCallable, HandlerContext
from app.dynamic.computed_fields.models import ComputedField, ServiceComputedField
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener


class ComputedFieldExecutionListener(Listener[RetrievedObjectsEvent]):
    """
    execute all computed fields for a retrieved object with the configured handlers
    """

    def __init__(self, computed_field_resolver: ComputedFieldResolver):
        self._computed_field_resolver = computed_field_resolver

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        model = event.context.response_model

        if not isinstance(model, DynamicObjectModel):
            return event

        computed_field_ids = model.service_config.get("computed_fields", None)
        if not computed_field_ids:
            return event

        rows = event.payload.rows
        if not rows:
            return event

        db = event.get_db()

        computed_fields: List[ComputedField] = self._computed_field_resolver.get_by_ids(computed_field_ids)
        processed_rows = self._execute_computed_fields(db, model, rows, computed_fields)

        event.payload.rows = processed_rows

        return event

    def _execute_computed_fields(
        self,
        db: Session,
        dynamic_obj_model: DynamicObjectModel,
        dynamic_objects: List[BaseModel],
        computed_fields: List[ComputedField],
    ) -> List[BaseModel]:
        # lookup correct handlers per field and give context
        for field in computed_fields:
            if isinstance(field, ServiceComputedField):
                context = HandlerContext(
                    db=db, dynamic_objects=dynamic_objects, dynamic_obj_model=dynamic_obj_model, computed_field=field
                )
                handler: ComputedFieldHandlerCallable = self._computed_field_resolver.get_handler(field.handler_id)
                handler(context=context)

        return dynamic_objects
