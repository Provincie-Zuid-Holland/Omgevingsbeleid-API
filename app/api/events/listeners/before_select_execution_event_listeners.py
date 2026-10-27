from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.api.events.before_select_execution_event import BeforeSelectExecutionEvent
from app.api.events.types import ApiListener
from app.core.tables.objects import ObjectStaticsTable
from app.core.types import DynamicObjectModel


class OptimizeSelectQueryListener(ApiListener[BeforeSelectExecutionEvent]):
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

    async def handle_event(
        self, session: AsyncSession, event: BeforeSelectExecutionEvent
    ) -> BeforeSelectExecutionEvent | None:
        if not event.context.response_model:
            return event

        if not event.context.objects_table_ref:
            return event

        if not isinstance(event.context.response_model, DynamicObjectModel):
            return event

        model_config: dict = event.context.response_model.service_config
        objects_table_reference = event.context.objects_table_ref

        static_fields: list[str] = [
            field_map["to_field"]
            for field_map in model_config.get("static_foreign_keys_extender", {}).get("fields_map", [])
        ]

        load_options: list[ExecutableOption] = []
        for field_map in model_config.get("foreign_keys_extender", {}).get("fields_map", []):
            load_options.append(selectinload(getattr(objects_table_reference, field_map["to_field"])))

        if inspect(objects_table_reference).mapper.class_ is ObjectStaticsTable:
            # static_only models are serialized from the statics row itself
            for field in static_fields:
                load_options.append(selectinload(getattr(objects_table_reference, field)))
        elif static_fields:
            for field in static_fields:
                load_options.append(
                    selectinload(objects_table_reference.object_statics).selectinload(
                        getattr(ObjectStaticsTable, field)
                    )
                )
        elif "object_statics" in event.context.response_model.pydantic_model.model_fields:
            load_options.append(selectinload(objects_table_reference.object_statics))

        event.payload.query = event.payload.query.options(*load_options)

        return event
