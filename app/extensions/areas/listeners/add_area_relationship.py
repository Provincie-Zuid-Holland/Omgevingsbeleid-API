from typing import Optional

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, relationship

from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event.types import Listener
from app.extensions.areas.db.tables import AreasTable


class AddAreasRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
        column = event.column
        if column.type != "area_uuid":
            return

        # Add the column itself
        additional_args = [ForeignKey(AreasTable.UUID)]
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
                    AreasTable,
                    primaryjoin=f"{event.table_name}.{column.name} == AreasTable.UUID",
                    viewonly=True,
                ),
            )
