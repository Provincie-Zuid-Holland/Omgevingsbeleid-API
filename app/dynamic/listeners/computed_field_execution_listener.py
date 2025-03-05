from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
from app.dynamic.computed_fields.models import ComputedField, ExecutionStrategy
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener


@dataclass
class ComputedFieldServiceConfig:
    computed_fields: Dict[str, ExecutionStrategy]


class ComputedFieldExecutionListener(Listener[RetrievedObjectsEvent]):
    """
    handle the execution of defined computed fields after receiving objects
    using the execution strategy defined in config.
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
        for field in computed_fields:
            # handle only service type fields since property types are triggered normally
            if field.execution_strategy == ExecutionStrategy.SERVICE:
                if field.handler_id is None:
                    raise RuntimeError(f"No registered handler ID for computed field '{field.id}'")

                # find configured handler and execute it
                handler = self._computed_field_resolver.get_handler(field.handler_id)
                handler(db, dynamic_objects, dynamic_obj_model, field)

        return dynamic_objects
