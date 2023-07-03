from typing import List

from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.orm import selectinload
from app.dynamic.db.object_static_table import ObjectStaticsTable

from app.dynamic.event.types import Listener
from app.dynamic.event import BeforeSelectExecutionEvent


class OptimizeSelectListener(Listener[BeforeSelectExecutionEvent]):
    def handle_event(
        self, event: BeforeSelectExecutionEvent
    ) -> BeforeSelectExecutionEvent:
        if not event.context.response_model:
            return event

        if not event.context.objects_table_ref:
            return event

        model_config: dict = event.context.response_model.service_config
        objects_table_reference = event.context.objects_table_ref
        load_options: List[ExecutableOption] = []
        for field_map in model_config.get("foreign_keys_extender", {}).get(
            "fields_map", []
        ):
            load_options.append(
                selectinload(getattr(objects_table_reference, field_map["to_field"]))
            )
        for field_map in model_config.get("static_foreign_keys_extender", {}).get(
            "fields_map", []
        ):
            load_options.append(
                selectinload(objects_table_reference.ObjectStatics).selectinload(
                    getattr(ObjectStaticsTable, field_map["to_field"])
                )
            )

        event.payload.query = event.payload.query.options(*load_options)

        return event
