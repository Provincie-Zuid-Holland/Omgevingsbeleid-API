from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import mapped_column, relationship

from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event.types import Listener


class AddObjectCodeRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, event: GenerateTableEvent) -> GenerateTableEvent:
        column = event.column
        if column.type != "object_code":
            return

        # Add the column itself
        additional_args = [ForeignKey("object_statics.Code")]
        setattr(
            event.table_type,
            column.name,
            mapped_column(column.name, Unicode(35), nullable=column.nullable, *additional_args),
        )

        # Add a viewonly relationship for easy access
        relation_field = column.type_data.get("relation_field", "")
        if relation_field:
            setattr(
                event.table_type,
                relation_field,
                relationship(
                    "ObjectStaticsTable",
                    primaryjoin=f"{event.table_name}.{column.name} == ObjectStaticsTable.Code",
                    viewonly=True,
                ),
            )
