from typing import Optional

from sqlalchemy import ForeignKey, Unicode, Uuid
from sqlalchemy.orm import mapped_column, relationship

from app.build.events.generate_table_event import GenerateTableEvent
from app.core.services.event.types import Listener
from app.core.tables.others import AreasTable, StorageFileTable
from app.core.tables.users import UsersTable
from sqlalchemy.orm import Session


class AddObjectCodeRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, session: Session, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
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


class AddAreasRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, session: Session, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
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


class AddUserRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, session: Session, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
        column = event.column
        if column.type != "user_uuid":
            return

        # Add the column itself
        additional_args = [ForeignKey("Gebruikers.UUID")]
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
                    UsersTable,
                    primaryjoin=f"{event.table_name}.{column.name} == UsersTable.UUID",
                    viewonly=True,
                ),
            )


class AddWerkingsgebiedenRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, session: Session, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
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


class AddStoreageFileRelationshipListener(Listener[GenerateTableEvent]):
    def handle_event(self, session: Session, event: GenerateTableEvent) -> Optional[GenerateTableEvent]:
        column = event.column
        if column.type != "file_uuid":
            return

        # Add the column itself
        fk_name = f"fk_{event.table_name}_{column.name}_to_storagefile_uuid"
        additional_args = [ForeignKey(StorageFileTable.UUID, name=fk_name)]
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
