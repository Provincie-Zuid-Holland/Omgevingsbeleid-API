from typing import Optional

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, relationship

from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event.types import Listener


class AddWerkingsgebiedenRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
        column = event.column
        if column.type != "werkingsgebied_uuid":
            return

        # Add the column itself
        additional_args = [ForeignKey("Werkingsgebieden.UUID")]
        setattr(
            event.table_type,
            column.name,
            mapped_column(column.name, Uuid, nullable=column.nullable, *additional_args),
        )

        # Add a viewonly relationship for easy access
        relation_field = column.type_data.get("relation_field", "")
        if relation_field:
            setattr(
                event.table_type,
                relation_field,
                relationship(
                    "SourceWerkingsgebiedenTable",
                    primaryjoin=f"{event.table_name}.{column.name} == SourceWerkingsgebiedenTable.UUID",
                    viewonly=True,
                ),
            )
