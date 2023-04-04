from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, relationship

from app.dynamic.event.generate_table_event import GenerateTableEvent
from app.dynamic.event.types import Listener
from app.extensions.users.db.tables import UsersTable


class AddUserRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, event: GenerateTableEvent) -> GenerateTableEvent:
        column = event.column
        if column.type != "user_uuid":
            return

        # Add the column itself
        additional_args = [ForeignKey("Gebruikers.UUID")]
        setattr(
            event.table_type,
            column.name,
            mapped_column(
                column.name, Uuid, nullable=column.nullable, *additional_args
            ),
        )

        # Add a viewonly relationship for easy access
        relation_field = column.type_data.get("relation_field", "")
        if relation_field:
            setattr(
                event.table_type,
                relation_field,
                relationship(
                    UsersTable,
                    primaryjoin=f"{event.table_name}.{column.name} == UsersTable.UUID",
                    viewonly=True,
                ),
            )
