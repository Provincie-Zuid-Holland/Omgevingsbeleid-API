from typing import Optional

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, relationship

from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event.types import Listener
from app.extensions.storage_files.db.tables import StorageFileTable


class AddStoreageFileRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
        column = event.column
        if column.type != "file_uuid":
            return

        # Add the column itself
        additional_args = [ForeignKey(StorageFileTable.UUID)]
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
                    StorageFileTable,
                    primaryjoin=f"{event.table_name}.{column.name} == StorageFileTable.UUID",
                    viewonly=True,
                ),
            )
