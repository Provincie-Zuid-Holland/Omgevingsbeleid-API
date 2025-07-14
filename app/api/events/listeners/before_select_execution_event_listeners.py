from typing import List, Optional

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.api.events.before_select_execution_event import BeforeSelectExecutionEvent
from app.core.services.event.types import Listener
from app.core.tables.objects import ObjectStaticsTable
from app.core.types import DynamicObjectModel


class OptimizeSelectQueryListener(Listener[BeforeSelectExecutionEvent]):
    """
    Optimizes the select query execution by dynamically
    adding `selectinload` options to the query based on the response model's
    configuration.

    This listener is triggered before the execution of a select query and
    modifies the query to include optimized loading strategies for related
    fields. It uses the `foreign_keys_extender` and `static_foreign_keys_extender`
    configurations from the response model's service configuration to determine
    which fields should be eagerly loaded.

    This will make sure that sqlalchemy is not going to run seperate queries for each row
    """

    def handle_event(self, session: Session, event: BeforeSelectExecutionEvent) -> Optional[BeforeSelectExecutionEvent]:
        if not event.context.response_model:
            return event

        if not event.context.objects_table_ref:
            return event

        if not isinstance(event.context.response_model, DynamicObjectModel):
            return event

        model_config: dict = event.context.response_model.service_config
        objects_table_reference = event.context.objects_table_ref

        load_options: List[ExecutableOption] = []
        for field_map in model_config.get("foreign_keys_extender", {}).get("fields_map", []):
            load_options.append(selectinload(getattr(objects_table_reference, field_map["to_field"])))
        for field_map in model_config.get("static_foreign_keys_extender", {}).get("fields_map", []):
            load_options.append(
                selectinload(objects_table_reference.ObjectStatics).selectinload(
                    getattr(ObjectStaticsTable, field_map["to_field"])
                )
            )

        event.payload.query = event.payload.query.options(*load_options)

        return event
